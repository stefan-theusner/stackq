# stackq

Ask questions about the [STACKIT docs](https://docs.stackit.cloud) from your terminal.
Everything runs locally: PostgreSQL + pgvector for the vector database and Ollama for the AI models.

## Stack

| Part | Version / tool |
|---|---|
| Python | 3.15.0 (pinned in `mise.toml`) |
| Database | PostgreSQL 18 + pgvector (`pgvector/pgvector:pg18`) |
| Embeddings | `nomic-embed-text` via Ollama |
| Chat model | `llama3.1:8b` via Ollama |
| CLI | typer + rich |

## Setup

1. Install [Ollama](https://ollama.com) **on your Mac** (it uses your GPU there) and pull the models:
   ```bash
   ollama pull nomic-embed-text
   ollama pull llama3.1:8b
   ```
2. Open this folder in VS Code and choose **Reopen in Container**.
   This starts Python 3.15 (via mise) and PostgreSQL 18 with pgvector; the schema in `db/init.sql` is applied automatically.
3. Inside the container:
   ```bash
   stackq version
   mise run test
   ```

## Usage (once implemented)

```bash
stackq scrape --limit 20   # stage 1: download docs to data/raw/
stackq index               # stages 2+3: chunk, embed, store
stackq ask "How do I create a SKE cluster?"
```

## Roadmap

- [ ] Scraper (`src/stackq/scraper.py`), start with `/sitemap.xml`
- [x] Chunker (`src/stackq/chunker.py`)
- [ ] DB insert + search (`src/stackq/db.py`)
- [ ] Indexing + ask (`src/stackq/rag.py`)
- [ ] Interactive chat mode, streaming answers, source list
