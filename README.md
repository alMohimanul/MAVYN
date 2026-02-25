# 📚 Lemma - Local-First Research Paper Manager

[![CI](https://github.com/yourusername/lemma/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/lemma/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A powerful, privacy-first research paper manager with semantic search and AI-powered insights.

Lemma helps researchers organize, search, and understand their paper collections using local semantic search and cloud LLMs - keeping your papers private while leveraging cutting-edge AI.

## ✨ Features

- 🔒 **Privacy-First**: All papers stored locally, no cloud uploads
- 🚀 **Fast Semantic Search**: FAISS-powered vector search across all papers
- 🤖 **AI-Powered Q&A**: Ask questions across your entire library using LLMs (Groq Compound Mini with tool support)
- 📊 **Smart Organization**: Automatic metadata extraction and intelligent file naming
- 🔄 **Incremental Updates**: Only processes new papers, never re-embeds existing ones
- 🎨 **Beautiful CLI**: Clean, intuitive interface built with Rich
- 🔌 **Multiple LLM Providers**: Groq, Gemini, OpenRouter with automatic fallback
- 📂 **Duplicate Detection**: SHA256 hash-based deduplication
- ⚡ **High Performance**: <100ms search across 1000+ papers

## 🎬 Demo

```bash
# Scan your papers directory
$ lemma scan ~/Papers/
✓ Scanned 42 PDFs: 5 new, 37 duplicates

# Generate embeddings (only for new papers)
$ lemma embed
✓ Embedded 5 papers

# Ask questions across your library
$ lemma ask "What are the main approaches to polyp segmentation?"
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/lemma.git
cd lemma

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

Set up your API keys (at least one is required for LLM features):

```bash
# .env file
GROQ_API_KEY=your_groq_key          # Primary (recommended)
GEMINI_API_KEY=your_gemini_key      # Backup
OPENROUTER_API_KEY=your_or_key      # Fallback
```

## Quick Start

```bash
# 1. Scan a folder for PDFs
lemma scan ~/Papers

# 2. List indexed papers
lemma list

# 3. Search by keyword
lemma search "transformer architecture"

# 4. View paper details
lemma info 5

# 5. Generate embeddings (required for semantic search)
lemma embed

# 6. Ask questions across your papers
lemma ask "What are the main approaches to visual question answering?"

# 7. Organize files with smart renaming
lemma organize --dry-run  # Preview changes
lemma organize            # Apply renames
```

## CLI Commands

### `lemma scan <directory>`
Scan a directory for PDFs and add them to the database.

**Options:**
- `--recursive/--no-recursive`: Scan subdirectories (default: true)
- `--db PATH`: Database path (default: `~/.lemma/lemma.db`)

### `lemma list`
List indexed papers in a table.

**Options:**
- `--limit N`: Max papers to show (default: 50)
- `--offset N`: Skip first N papers
- `--sort-by FIELD`: Sort by `indexed_at`, `year`, or `title`

### `lemma search <query>`
Search papers by keyword (searches title, authors, abstract).

### `lemma info <paper_id>`
Show detailed information about a specific paper.

### `lemma embed`
Generate embeddings for semantic search.

**Options:**
- `--force`: Re-embed papers that already have embeddings

### `lemma ask <question>`
Ask a question across all papers using semantic search + LLM synthesis.

**Options:**
- `--top-k N`: Number of papers to retrieve (default: 5)

### `lemma organize`
Rename PDF files based on metadata.

**Options:**
- `--dry-run`: Preview changes without applying
- `--pattern PATTERN`: Custom filename pattern (default: `{year}_{first_author}_{short_title}.pdf`)

## Architecture

```
src/lemma/
├── cli/           # Click-based CLI commands
├── core/          # Core functionality (scanner, extractor, organizer)
├── db/            # SQLite schema and repository
├── embeddings/    # sentence-transformers + FAISS
└── llm/           # Provider rotation (Groq → Gemini → OpenRouter)
```

## Design Principles

1. **Local-first**: Embeddings and search run entirely on your machine
2. **LLM only for reasoning**: Cloud APIs used sparingly for synthesis
3. **Cost optimization**: Regex-first extraction, content hashing, response caching
4. **Graceful degradation**: System works offline after initial indexing
5. **Provider rotation**: Automatic fallback if rate limits hit

## Optimization Strategy

- **Regex-first extraction**: ~80% of metadata extracted locally
- **Content hashing**: SHA256 deduplication prevents reprocessing
- **Response caching**: SQLite cache with TTL
- **Batching**: Process multiple papers per LLM call
- **Provider failover**: Automatic rotation on rate limits

## Expected Usage

For a collection of 200 papers:
- Metadata extraction: mostly local (fast)
- Embeddings: local (one-time, ~2-5 minutes)
- LLM calls: ~300 calls total for summaries/Q&A
- Cost: $0 (within free tier limits)

## Requirements

- Python 3.10+
- ~500MB disk space (for models)
- API keys for at least one LLM provider (optional for basic features)

## Development

```bash
# Run tests
pytest tests/

# Format code
black src/ tests/

# Type checking
mypy src/
```

## License

MIT License - see LICENSE file for details

## Roadmap

**Week 1 (MVP):** ✅ **COMPLETE**
- [x] Project structure
- [x] PDF scanning & deduplication
- [x] Metadata extraction
- [x] CLI commands (scan, list, search, info)
- [x] Embeddings integration
- [x] LLM-powered Q&A
- [x] File organization

**Week 2 (Enhancements):**
- [ ] Citation extraction
- [ ] ArXiv API integration
- [ ] Paper comparison
- [ ] Collection summaries

**Future:**
- [ ] Topic auto-classification
- [ ] Shell completions
- [ ] Web UI
- [ ] Export to bibliography formats
