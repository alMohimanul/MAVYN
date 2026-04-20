"""File system watcher for monitoring paper directories."""
import time
from pathlib import Path
from typing import Callable, Optional, Set
from threading import Thread, Event

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PDFEventHandler(FileSystemEventHandler):
    """Handler for PDF file system events."""

    def __init__(self, callback: Callable[[Path], None], debounce_seconds: float = 2.0):
        """Initialize the event handler.

        Args:
            callback: Function to call when a new PDF is detected
            debounce_seconds: Minimum time between processing the same file
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._processing_files: Set[str] = set()
        self._last_processed: dict[str, float] = {}

    def _should_process(self, file_path: Path) -> bool:
        """Check if a file should be processed.

        Args:
            file_path: Path to check

        Returns:
            True if file should be processed
        """
        # Only process PDF files
        if file_path.suffix.lower() != ".pdf":
            return False

        # Check if file exists and is not empty
        if not file_path.exists() or file_path.stat().st_size == 0:
            return False

        # Debounce: Don't process same file too quickly
        file_str = str(file_path)
        last_time = self._last_processed.get(file_str, 0)
        current_time = time.time()

        if current_time - last_time < self.debounce_seconds:
            return False

        # Don't process if already being processed
        if file_str in self._processing_files:
            return False

        return True

    def _process_file(self, file_path: Path):
        """Process a file with debouncing.

        Args:
            file_path: Path to process
        """
        file_str = str(file_path)

        try:
            self._processing_files.add(file_str)
            self._last_processed[file_str] = time.time()

            logger.info(f"Detected new PDF: {file_path.name}")
            self.callback(file_path)

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)

        finally:
            self._processing_files.discard(file_str)

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_process(file_path):
                # Small delay to ensure file is fully written
                time.sleep(0.5)
                self._process_file(file_path)

    def on_moved(self, event):
        """Handle file move events (downloads often appear as moves)."""
        if not event.is_directory:
            file_path = Path(event.dest_path)
            if self._should_process(file_path):
                # Small delay to ensure file is fully written
                time.sleep(0.5)
                self._process_file(file_path)


class DirectoryWatcher:
    """Watches a directory for new PDF files."""

    def __init__(
        self,
        directory: Path,
        callback: Callable[[Path], None],
        recursive: bool = True,
        debounce_seconds: float = 2.0,
    ):
        """Initialize the directory watcher.

        Args:
            directory: Directory to watch
            callback: Function to call when new PDF detected
            recursive: Whether to watch subdirectories
            debounce_seconds: Minimum time between processing same file
        """
        self.directory = Path(directory).expanduser().resolve()
        self.callback = callback
        self.recursive = recursive
        self.debounce_seconds = debounce_seconds

        # Validate directory
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")
        if not self.directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.directory}")

        # Initialize watchdog
        self.event_handler = PDFEventHandler(callback, debounce_seconds)
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler, str(self.directory), recursive=recursive
        )

        self._is_running = False

    def start(self):
        """Start watching the directory."""
        if self._is_running:
            logger.warning("Watcher already running")
            return

        logger.info(
            f"Starting watcher on: {self.directory} " f"(recursive={self.recursive})"
        )

        self.observer.start()
        self._is_running = True

    def stop(self):
        """Stop watching the directory."""
        if not self._is_running:
            return

        logger.info("Stopping watcher")
        self.observer.stop()
        self.observer.join()
        self._is_running = False

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._is_running


class PeriodicScanner:
    """Periodically scans a directory for new PDFs (alternative to watchdog)."""

    def __init__(
        self,
        directory: Path,
        callback: Callable[[Path], None],
        scan_interval: int = 60,
        recursive: bool = True,
    ):
        """Initialize the periodic scanner.

        Args:
            directory: Directory to scan
            callback: Function to call for each new PDF
            scan_interval: Seconds between scans
            recursive: Whether to scan subdirectories
        """
        self.directory = Path(directory).expanduser().resolve()
        self.callback = callback
        self.scan_interval = scan_interval
        self.recursive = recursive

        # Validate directory
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")
        if not self.directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.directory}")

        # Track seen files
        self._seen_files: Set[str] = set()
        self._stop_event = Event()
        self._scan_thread: Optional[Thread] = None

    def _scan_once(self):
        """Perform a single scan of the directory."""
        try:
            # Find all PDFs
            pattern = "**/*.pdf" if self.recursive else "*.pdf"
            pdf_files = list(self.directory.glob(pattern))

            # Process new files
            for pdf_path in pdf_files:
                file_str = str(pdf_path)

                # Skip if already seen
                if file_str in self._seen_files:
                    continue

                # Skip if file doesn't exist or is empty
                if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                    continue

                # Mark as seen
                self._seen_files.add(file_str)

                # Process file
                try:
                    logger.info(f"Detected new PDF: {pdf_path.name}")
                    self.callback(pdf_path)
                except Exception as e:
                    logger.error(f"Error processing {pdf_path}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error scanning directory: {e}", exc_info=True)

    def _scan_loop(self):
        """Main scanning loop."""
        logger.info(
            f"Starting periodic scanner on: {self.directory} "
            f"(interval={self.scan_interval}s, recursive={self.recursive})"
        )

        # Initial scan to populate seen files
        self._scan_once()

        while not self._stop_event.is_set():
            # Wait for interval or stop event
            if self._stop_event.wait(timeout=self.scan_interval):
                break

            # Perform scan
            self._scan_once()

    def start(self):
        """Start periodic scanning."""
        if self._scan_thread and self._scan_thread.is_alive():
            logger.warning("Scanner already running")
            return

        self._stop_event.clear()
        self._scan_thread = Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()

    def stop(self):
        """Stop periodic scanning."""
        if not self._scan_thread:
            return

        logger.info("Stopping scanner")
        self._stop_event.set()

        if self._scan_thread.is_alive():
            self._scan_thread.join(timeout=5)

    def is_running(self) -> bool:
        """Check if scanner is running."""
        return self._scan_thread is not None and self._scan_thread.is_alive()
