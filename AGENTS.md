# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What this is

`stackq` is a local RAG CLI for asking questions about the STACKIT docs (https://docs.stackit.cloud). It is a learning project: most pipeline stages are deliberately left as `TODO` / `NotImplementedError` stubs with hints in their docstrings and comments. See the README roadmap for what's done. Only `chunker.py` is implemented so far.

## Commands

Tasks are defined in `mise.toml` (mise also creates and activates `.venv`):

```bash
mise run install          # pip install -e '.[dev]'
mise run test             # pytest
mise run lint             # ruff check . && ruff format --check .
pytest tests/test_chunker.py::test_chunks_overlap   # single test
stackq --help             # CLI entry point (stackq.cli:app)
```

Ruff line length is 100. Python is pinned to 3.15.0 (`requires-python >=3.15`).

## Environment

- Normally developed in the VS Code devcontainer (`.devcontainer/`): an `app` container plus a `db` container running `pgvector/pgvector:pg18`. `db/init.sql` is applied only on first creation of the `pgdata` volume, so schema changes need the volume recreated (or a manual migration).
- Ollama runs on the **host Mac** (for the GPU), not in a container. Inside the devcontainer, `OLLAMA_HOST=http://host.docker.internal:11434` and `DATABASE_URL=...@db:5432/...`; `mise.toml` and `config.py` fall back to `localhost` outside it.
- Models are overridable via `STACKQ_EMBED_MODEL` (default `nomic-embed-text`) and `STACKQ_CHAT_MODEL` (default `llama3.1:8b`).

## Architecture

A four-stage pipeline, each stage in its own module, wired together by `cli.py` (typer). CLI commands import their stage module lazily inside the function so `stackq version` works without DB/Ollama.

1. **Scrape** (`scraper.py`, `stackq scrape --limit N`): read `/sitemap.xml`, fetch pages, extract main content, write one JSON per page (`{url, title, text}`) to `data/raw/` (gitignored). Should sleep between requests.
2. **Chunk** (`chunker.py`): fixed-size character chunks with overlap (default 800/150).
3. **Embed + store** (`rag.index_all` → `rag.embed` → `db.insert_chunk`, `stackq index`): embeddings via the Ollama client, stored in the single `stackq_embeddings` table.
4. **Ask** (`rag.ask`, `stackq ask "..."`): embed question → `db.search` (cosine distance `<=>`, HNSW index with `vector_cosine_ops`) → fill `rag.PROMPT` with context → `client.chat`. The prompt requires answers only from context, with cited source URLs.

Key coupling: `stackq_embeddings.embedding` is `vector(768)`, matching `nomic-embed-text`. Changing `EMBED_MODEL` to a model with a different dimension requires changing `db/init.sql` and re-indexing. `db.connect()` calls `register_vector` so Python lists/arrays map to the pgvector type.
