# 📚 MAVYN - Your AI Research Assistant

> A privacy-first research paper manager with natural language interface and local semantic search.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🔒 **Privacy-First**: All papers stored locally, no cloud uploads
- 💬 **Natural Language Interface**: Interactive REPL - just chat with your papers
- 🚀 **Fast Semantic Search**: Local vector search across all papers
- 🤖 **AI Q&A**: Ask questions naturally without command prefixes
- 📊 **Paper Comparison**: Compare multiple papers with intelligent caching
- 🔗 **Similar Papers**: Find related work in your library with optional arXiv suggestions
- 📈 **Auto-Processing**: One command to scan, rename, and embed
- 🔄 **Incremental Updates**: 70-90% faster re-embedding
- 📂 **Smart Cleanup**: Automatically removes deleted papers from database

## 🚀 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Start MAVYN

```bash
mavyn
```

This launches the interactive assistant.

### 3. Initial Setup

```
MAVYN> /sync ~/Papers

# Your papers are now:
# ✓ Scanned and indexed
# ✓ Renamed with metadata
# ✓ Embedded for semantic search
# ✓ Ready for questions
```

### 4. List Your Papers

```
MAVYN> /list

# Shows numbered list of all papers
```

### 5. Ask Questions Naturally

```
MAVYN> tell me the methodology summary of paper 4

MAVYN> compare papers 1 and 5

MAVYN> find similar papers about transformers

MAVYN> what are the main findings in paper 7?
```

**No command prefixes needed!** Just type your question naturally.

## 📖 Complete Workflow

### First-Time Setup
```
$ mavyn

MAVYN> /sync ~/Papers

# MAVYN will:
# 1. Scan all PDFs in ~/Papers
# 2. Extract metadata (title, authors, year, etc.)
# 3. Rename files for easy identification
# 4. Generate embeddings for semantic search
```

### Daily Use
```
$ mavyn

MAVYN> /list
# See all your papers with IDs

MAVYN> what is the main contribution of paper 5?
# Get AI-powered summaries

MAVYN> compare the methodology in papers 2 and 7
# Side-by-side comparisons

MAVYN> find papers similar to paper 3
# Discover related work

MAVYN> /exit
# Exit when done
```

### Auto-Sync New Papers
```
MAVYN> /sync ~/Papers --watch

# Now just drop new PDFs into ~/Papers
# They'll be automatically processed!
```

## 🔧 Available Commands

### Slash Commands
- `/sync [directory]` - Setup and sync your papers
- `/sync --watch` - Continuously monitor for new papers
- `/list` - List all indexed papers with IDs
- `/help` - Show help message
- `/exit` - Exit MAVYN

### Natural Language Queries
No special syntax needed! Just ask naturally:
- "tell me about paper 5"
- "summarize the methodology of paper 3"
- "compare papers 1, 4, and 7"
- "find papers similar to paper 2"
- "what are the key contributions in paper 6?"

## 🤖 AI Q&A Setup (Optional)

Set up an API key to enable AI-powered question answering:

```bash
# Option 1: Environment variable
export GROQ_API_KEY="your_key_here"

# Option 2: .env file
echo "GROQ_API_KEY=your_key_here" > ~/.MAVYN/.env
```

**Get Free API Keys:**
- [Groq](https://console.groq.com/) - Fast and generous free tier (recommended)
- [Google Gemini](https://makersuite.google.com/) - Alternative option

Without API keys, MAVYN will still:
- Index and search papers
- Show relevant papers for your queries
- Perform all local operations

## 🔒 Privacy

- **All papers stay on your machine** - never uploaded anywhere
- **Embeddings generated locally** - no external API calls
- **Cloud APIs only for Q&A** - and only if you configure them
- **Similar papers + arXiv (optional)** - If enabled, MAVYN sends a **keyword search query** (derived from your question or seed paper title/abstract) to **export.arxiv.org**. No PDFs are uploaded. Responses are cached locally for 24 hours.
- **Database stored locally** at `~/.MAVYN/MAVYN.db`

## 📦 Requirements

- Python 3.10 or higher
- ~500MB disk space for embedding models
- Internet connection only for optional AI Q&A and optional arXiv similar-paper search

## 🎯 Example Session

```
$ mavyn

Welcome to MAVYN - Your AI Research Assistant

Available Commands:
- /sync [directory] - Setup and sync your papers
- /list - List all indexed papers
- /help - Show help message
- /exit - Exit MAVYN

Natural Language Queries:
Just type your question naturally!

MAVYN> /sync ~/Documents/Papers
📂 Scanning: /Users/you/Documents/Papers
✓ paper1.pdf [renamed] [embedded]
✓ paper2.pdf [renamed] [embedded]
✓ paper3.pdf [renamed] [embedded]

Sync Summary
────────────
Total files: 3
New papers: 3
Embedded: 3

MAVYN> /list
┌────┬──────────────────────────────────────┬────────────┬──────┐
│ ID │ Title                                │ Authors    │ Year │
├────┼──────────────────────────────────────┼────────────┼──────┤
│ 1  │ Attention Is All You Need            │ Vaswani et │ 2017 │
│ 2  │ BERT: Pre-training of Deep Bidirect  │ Devlin et  │ 2018 │
│ 3  │ GPT-3: Language Models are Few-Shot  │ Brown et a │ 2020 │
└────┴──────────────────────────────────────┴────────────┴──────┘

MAVYN> tell me about the methodology in paper 1

[AI generates detailed methodology summary...]

MAVYN> compare papers 1 and 2

[AI generates side-by-side comparison...]

MAVYN> /exit
Goodbye!
```

## 🛠️ Advanced Features

### Incremental Updates
MAVYN is smart about re-processing papers:
- Only embeds new or modified papers
- Reuses unchanged content chunks
- 70-90% faster when updating existing papers

### Paper Comparison Caching
When you compare papers, results are cached:
- Instant results for repeat comparisons
- Reduces API costs
- Cached for 24 hours

### arXiv Integration
Find related papers beyond your library:
- Set `MAVYN_ARXIV_RELATED=1` or use `--arxiv` flag (when available)
- MAVYN queries arXiv API with keyword search
- Results are deduplicated against your library
- Ranked by semantic similarity

## 🗺️ Project Structure

```
MAVYN/
├── ~/.MAVYN/              # User data directory
│   ├── MAVYN.db          # Local database
│   ├── search.index      # FAISS vector index
│   └── .env              # Optional API keys
└── src/MAVYN/            # Source code
    ├── cli/              # Interactive REPL & commands
    ├── core/             # PDF processing & sync
    ├── db/               # Database & models
    ├── embeddings/       # Vector search
    ├── llm/              # AI providers & caching
    └── integrations/     # arXiv client
```

## 📝 License

MIT License - see LICENSE file for details

## 💬 Support

- Report issues: [GitHub Issues](https://github.com/alMohimanul/mavyn/issues)
- Questions: Open a discussion on GitHub

## 🙏 Acknowledgments

MAVYN builds on open source technologies:
- Sentence Transformers for embeddings
- FAISS for vector search
- Rich for beautiful terminal UI
- Click for CLI framework
