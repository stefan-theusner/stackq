# stackq

Ask questions about the [STACKIT docs](https://docs.stackit.cloud) from your terminal.
Everything runs locally: PostgreSQL + pgvector for the vector database and Ollama for the AI models.

## Stack

| Part | Version / tool |
|---|---|
| Python | 3.12.15 (pinned in `mise.toml`) |
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
   This starts Python 3.12 (via mise) and PostgreSQL 18 with pgvector; the schema in `db/init.sql` is applied automatically.
3. Inside the container:
   ```bash
   stackq version
   mise run test
   ```

## Usage

```bash
stackq scrape --limit 20   # stage 1: download docs to data/raw/
stackq index               # stage 2: chunk, embed, store
stackq ask "How do I create a SKE cluster?"
stackq evaluate            # retrieval hit rate over evals/retrieval.json
```

## Roadmap

- [x] Scraper (`src/stackq/scraper.py`), reads `/sitemap-0.xml`
- [x] Chunking + embedding + storing (`src/stackq/indexer.py`)
- [x] Search (`src/stackq/db.py`): parent-child retrieval with pgvector
- [x] Ask (`src/stackq/rag.py`)
- [x] Retrieval eval (`src/stackq/evaluate.py`, `evals/retrieval.json`)
- [ ] Interactive chat mode, streaming answers, source list
- [ ] Reranker (two of the three remaining misses are in the top 20)

## How retrieval works

- **Parent-child chunks:** pages are split by `#`/`##`/`###` headers into sections (parents), and each
  section into 400-character chunks (children). Only children are embedded; a search returns their
  parent sections, so the model gets the full context around a match.
- **Embedding text:** children are embedded as
  `search_document: <product path> > <heading path>\n<chunk>` (e.g. `security > kms > how-tos > Create
  and manage keys > ...`), questions as `search_query: <question>`. These are the task prefixes
  `nomic-embed-text` was trained with; the paths give each chunk its product and section context.
- **Context:** the 10 nearest children decide which parent sections go to the model, serialized as
  [TOON](https://github.com/toon-format/toon).

## Evaluation

`stackq evaluate [--k N]` embeds each question in `evals/retrieval.json`, searches like `stackq ask`
does, and counts a hit if one of the question's expected URLs is among the retrieved pages. Misses list
the URLs that came back.

| Step | Hit rate |
|---|---|
| First run, 13 questions, k=5 | 9/13 (69%) |
| Test data fixed (questions accept several correct pages) | 11/13 (85%) |
| Product path added to the embedding text | 11/13 (no change) |
| 42 questions, k=5 | 39/42 (93%) |
| Query rewriting by the chat model (tried, removed) | 39/42 (no change) |
| k=10 (current default) | 40/42 (95%) |
| k=20 | 41/42 (98%) |

The remaining misses are vocabulary gaps between question and docs, e.g. "which clients can access a
file share" vs. File Storage's "export policies". Query rewriting didn't close them: the chat model
doesn't know STACKIT's own terms.
