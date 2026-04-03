"""Sync orchestrator for automatic paper processing."""
import signal
import sys
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from .pipeline import PaperProcessingPipeline
from .watcher import DirectoryWatcher, PeriodicScanner
from ..db.repository import Repository
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SyncOrchestrator:
    """Orchestrates automatic paper processing and monitoring."""

    def __init__(
        self,
        repo: Repository,
        auto_rename: bool = True,
        rename_pattern: str = "{year}_{first_author}_{short_title}.pdf",
        embed_immediately: bool = True,
        chunking_strategy: str = "hybrid",
        index_path: str = "~/.lemma/search.index",
        use_watchdog: bool = True,
        scan_interval: int = 60,
    ):
        """Initialize the sync orchestrator.

        Args:
            repo: Database repository
            auto_rename: Whether to automatically rename files
            rename_pattern: Pattern for renaming files
            embed_immediately: Whether to embed immediately
            chunking_strategy: Chunking strategy (hybrid, structure, sentence, simple)
            index_path: Path to FAISS index
            use_watchdog: Whether to use watchdog (vs periodic scanning)
            scan_interval: Scan interval for periodic mode (seconds)
        """
        self.repo = repo
        self.use_watchdog = use_watchdog
        self.scan_interval = scan_interval

        # Initialize pipeline
        self.pipeline = PaperProcessingPipeline(
            repo=repo,
            auto_rename=auto_rename,
            rename_pattern=rename_pattern,
            embed_immediately=embed_immediately,
            chunking_strategy=chunking_strategy,
            index_path=index_path,
        )

        # Watcher/scanner (created on demand)
        self._watcher: Optional[DirectoryWatcher] = None
        self._scanner: Optional[PeriodicScanner] = None

    def sync_directory_once(
        self,
        directory: Path,
        recursive: bool = True,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Sync a directory once (no continuous monitoring).

        Args:
            directory: Directory to sync
            recursive: Whether to scan subdirectories
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"Starting one-time sync of: {directory}")

        # Run auto-migration if needed
        self._auto_migrate()

        # Process directory
        if progress_callback:
            progress_callback("scanning", {"directory": str(directory)})

        results = self.pipeline.process_directory(directory, recursive=recursive)

        if progress_callback:
            progress_callback("completed", results)

        logger.info(
            f"Sync completed: {results['success']} new, "
            f"{results['duplicate']} duplicates, {results['failed']} failed"
        )

        # Update config
        self._update_sync_stats(directory, results)

        return results

    def start_watching(
        self,
        directory: Path,
        recursive: bool = True,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> None:
        """Start continuous monitoring of a directory.

        Args:
            directory: Directory to watch
            recursive: Whether to watch subdirectories
            progress_callback: Optional callback for progress updates
        """
        logger.info(f"Starting continuous watch of: {directory}")

        # Run auto-migration if needed
        self._auto_migrate()

        # Initial sync
        logger.info("Performing initial sync...")
        initial_results = self.sync_directory_once(
            directory, recursive, progress_callback
        )

        logger.info(
            f"Initial sync: {initial_results['success']} new, "
            f"{initial_results['duplicate']} duplicates"
        )

        # Define callback for new files
        def on_new_file(file_path: Path):
            try:
                if progress_callback:
                    progress_callback("processing", {"file": str(file_path)})

                result = self.pipeline.process_file(file_path)

                if progress_callback:
                    if result.success:
                        progress_callback(
                            "file_completed",
                            {
                                "file": str(file_path),
                                "paper_id": result.paper_id,
                                "renamed": result.renamed,
                                "embedded": result.embedded,
                            },
                        )
                    else:
                        progress_callback(
                            "file_failed",
                            {
                                "file": str(file_path),
                                "error": result.error,
                            },
                        )

            except Exception as e:
                logger.error(f"Error in file callback: {e}", exc_info=True)
                if progress_callback:
                    progress_callback(
                        "file_failed",
                        {
                            "file": str(file_path),
                            "error": str(e),
                        },
                    )

        # Start watcher/scanner
        if self.use_watchdog:
            try:
                self._watcher = DirectoryWatcher(
                    directory=directory,
                    callback=on_new_file,
                    recursive=recursive,
                    debounce_seconds=2.0,
                )
                self._watcher.start()

                logger.info("Watchdog monitoring started")

                if progress_callback:
                    progress_callback(
                        "watching", {"directory": str(directory), "mode": "watchdog"}
                    )

            except Exception as e:
                logger.error(f"Failed to start watchdog: {e}")
                logger.info("Falling back to periodic scanning")
                self.use_watchdog = False

        if not self.use_watchdog:
            self._scanner = PeriodicScanner(
                directory=directory,
                callback=on_new_file,
                scan_interval=self.scan_interval,
                recursive=recursive,
            )
            self._scanner.start()

            logger.info(f"Periodic scanning started (interval: {self.scan_interval}s)")

            if progress_callback:
                progress_callback(
                    "watching",
                    {
                        "directory": str(directory),
                        "mode": "periodic",
                        "interval": self.scan_interval,
                    },
                )

        # Add directory to watched list
        self._add_watched_directory(directory)

    def stop_watching(self):
        """Stop continuous monitoring."""
        logger.info("Stopping monitoring...")

        if self._watcher and self._watcher.is_running():
            self._watcher.stop()
            self._watcher = None

        if self._scanner and self._scanner.is_running():
            self._scanner.stop()
            self._scanner = None

        logger.info("Monitoring stopped")

    def is_watching(self) -> bool:
        """Check if currently watching a directory."""
        if self._watcher and self._watcher.is_running():
            return True
        if self._scanner and self._scanner.is_running():
            return True
        return False

    def _auto_migrate(self):
        """Automatically run database migration if needed."""
        try:
            from ..db.migrate import check_migration_status, migrate_to_versioning

            status = check_migration_status(self.repo.engine.url.database)

            if status["needs_migration"]:
                logger.info("Running automatic database migration...")
                success = migrate_to_versioning(self.repo.engine.url.database)

                if success:
                    logger.info("Database migration completed successfully")
                else:
                    logger.warning(
                        "Database migration failed - some features may not work"
                    )

        except Exception as e:
            logger.warning(f"Auto-migration check failed: {e}")

    def _add_watched_directory(self, directory: Path):
        """Add directory to list of watched directories in config."""
        try:
            watched = self.repo.get_config("watched_directories", [])

            if isinstance(watched, str):
                watched = [watched]

            directory_str = str(directory)

            if directory_str not in watched:
                watched.append(directory_str)
                self.repo.set_config("watched_directories", watched)

                logger.info(f"Added to watched directories: {directory_str}")

        except Exception as e:
            logger.warning(f"Failed to update watched directories: {e}")

    def _update_sync_stats(self, directory: Path, results: dict):
        """Update sync statistics in config."""
        try:
            stats = {
                "last_sync": datetime.utcnow().isoformat(),
                "directory": str(directory),
                "total": results.get("total", 0),
                "success": results.get("success", 0),
                "duplicate": results.get("duplicate", 0),
                "failed": results.get("failed", 0),
                "renamed": results.get("renamed", 0),
                "embedded": results.get("embedded", 0),
            }

            self.repo.set_config("last_sync_stats", stats)

        except Exception as e:
            logger.warning(f"Failed to update sync stats: {e}")

    def get_watched_directories(self) -> List[str]:
        """Get list of watched directories from config."""
        watched = self.repo.get_config("watched_directories", [])

        if isinstance(watched, str):
            return [watched]

        return watched if isinstance(watched, list) else []

    def get_last_sync_stats(self) -> Optional[Dict[str, Any]]:
        """Get last sync statistics from config."""
        stats = self.repo.get_config("last_sync_stats")
        return stats if isinstance(stats, dict) else None


def setup_signal_handlers(orchestrator: SyncOrchestrator):
    """Setup signal handlers for graceful shutdown.

    Args:
        orchestrator: Sync orchestrator instance
    """

    def signal_handler(signum, frame):
        logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
        orchestrator.stop_watching()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
