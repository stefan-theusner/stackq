# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What this is

`stackq` is a local RAG CLI for asking questions about the STACKIT docs (https://docs.stackit.cloud). It is a learning project; see the README roadmap for what's done. Scraping, indexing, asking and a retrieval eval are implemented.

## Commands

Tasks are defined in `mise.toml` (mise also creates and activates `.venv`):

```bash
mise run install          # pip install -r requirements-dev.txt && pip install -e . --no-deps
mise run test             # pytest
mise run lint             # ruff check . && ruff format --check .
pytest tests/test_scraper.py::test_url_to_file_name_uses_full_path   # single test
stackq --help             # CLI entry point (stackq.cli:app)
```

Ruff line length is 100. Python is pinned to 3.12.15 (`requires-python >=3.12`).

## Environment

- Normally developed in the VS Code devcontainer (`.devcontainer/`): an `app` container plus a `db` container running `pgvector/pgvector:pg18`. The `app` image (`.devcontainer/Dockerfile`) runs as the non-root user `stackq` and bakes in psql 18 and mise + Python; mise shims and `.venv/bin` are on `PATH` via `ENV`, so every shell (IDE terminal, `docker exec`) finds Python. `db/init.sql` is applied only on first creation of the `pgdata` volume, so schema changes need the volume recreated (or a manual migration).
- Ollama runs on the **host Mac** (for the GPU), not in a container. Inside the devcontainer, `OLLAMA_HOST=http://host.docker.internal:11434` and `DATABASE_URL=...@db:5432/...`; `mise.toml` and `config.py` fall back to `localhost` outside it.
- Models are overridable via `STACKQ_EMBED_MODEL` (default `nomic-embed-text`) and `STACKQ_CHAT_MODEL` (default `llama3.1:8b`).

## Architecture

A three-stage pipeline plus an eval, each stage in its own module, wired together by `cli.py` (typer). CLI commands import their stage module lazily inside the function so `stackq version` works without DB/Ollama.

1. **Scrape** (`scraper.py`, `stackq scrape --limit N`): read `/sitemap-0.xml` (the only sitemap `/sitemap-index.xml` lists), fetch pages (one module-level `requests.Session`, UA `stackq/<version>`, 1 s pause), extract the main content as Markdown, and write two files per page to `data/raw/<category>/<url path after the category, with / replaced by ->` (e.g. `products/runtime-kubernetes-engine-faq`): a `.md` (YAML front matter `title`/`source`, then the content; written first) and a `.json` (`{url, category, title, md}`; written last, so it marks a complete page). The data dir is relative to the working directory, overridable via `STACKQ_DATA_DIR`. Locale prefixes are an explicit list (`scraper.LOCALES`). `stackq scrape` exits 1 if any page failed. `file_util.MetaMarkdownPair.read_content` strips the front matter before indexing.
2. **Index** (`indexer.py`, `stackq index`): for each `.json`/`.md` pair in the data dir, delete the page from `stackq_pages` (cascades to its chunks), insert it again, split the Markdown by `#`/`##`/`###` headers into parent sections (stored in `stackq_embeddings` without embedding) and each section into 400/50-character child chunks (embedded with `ollama.embed`, `parent_id` pointing to their section). Children are embedded as `search_document: <product path from the URL> > <heading path>\n<chunk>`; the stored `content` is the plain chunk. One transaction per page; on error it rolls back and continues. `stackq index` exits 1 if any page failed.
3. **Ask** (`rag.ask`, `stackq ask "..."`): embed the question as `search_query: <question>` → `db.search` (k=10 nearest children by cosine distance `<=>`, HNSW index with `vector_cosine_ops`, returns their distinct parent sections) → each row as a TOON-serialized `user` message after the `SYS_MESSAGES` system prompt and the question → `client.chat` with `num_ctx` 8192. The system prompt requires answers only from context, with cited source URLs.
4. **Evaluate** (`evaluate.py`, `stackq evaluate --k N`): for each case in `evals/retrieval.json` (`{question, urls}`), run `rag.retrieve` (same path as `ask`) and count a hit if any expected URL is retrieved; misses print the returned URLs. Results history is in the README.

The `search_document:`/`search_query:` prefixes are the task prefixes `nomic-embed-text` expects; changing them, the product/heading path, or the chunking requires a re-index (`stackq index`).

Key coupling: `stackq_embeddings.embedding` is `vector(768)`, matching `nomic-embed-text`. Changing `EMBED_MODEL` to a model with a different dimension requires changing `db/init.sql` and re-indexing. `db.connect()` calls `register_vector` so Python lists/arrays map to the pgvector type.


## Troubleshooting

If db is not correct run to down the container and remove the volume
```
docker compose -p devcontainer -f .devcontainer/docker-compose.yml down -v
```