# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Lemma
- PDF scanning and hash-based deduplication
- Metadata extraction from PDFs
- Semantic search using sentence-transformers
- FAISS-based vector search index
- LLM integration (Groq Compound Mini, Google Gemini)
- Smart paper organization with customizable naming patterns
- Command-line interface with multiple commands:
  - `scan`: Scan directories for PDF papers
  - `embed`: Generate embeddings for semantic search
  - `search`: Semantic search across papers
  - `ask`: Interactive LLM-powered Q&A
  - `list`: List all papers in library
  - `organize`: Smart file organization
  - `export`: Export library metadata
- SQLite database for efficient paper management
- Incremental updates (only new papers are processed)
- Dry-run mode for safe testing
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Full documentation and contribution guidelines

### Features
- **Local-First**: All data stored locally, full privacy control
- **Semantic Search**: Natural language queries across your paper library
- **LLM Reasoning**: Ask questions about papers with context-aware responses
- **Smart Organization**: Automatic file naming based on metadata
- **Incremental Processing**: Efficient updates when adding new papers
- **Multiple LLM Providers**: Support for Groq and Gemini with easy extensibility
- **Hash-Based Deduplication**: Prevents duplicate papers using SHA256
- **Batch Processing**: Efficient handling of large paper collections

## [0.1.0] - 2024-02-25

### Added
- Initial project structure
- Core scanning, extraction, and embedding functionality
- Basic CLI commands
- Database models and repository pattern
- LLM provider abstraction
- Documentation and setup files

---

## Version History

- `0.1.0` - Initial alpha release with core functionality
- Future versions will be documented here

## How to Read This Changelog

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

For the complete list of changes in each release, see the [GitHub Releases](https://github.com/yourusername/lemma/releases) page.
