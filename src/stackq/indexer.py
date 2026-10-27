from urllib.parse import urlparse

import ollama
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from stackq.config import EMBED_MODEL
from stackq.db import connect, insert_chunk, insert_chunk_parent, insert_page
from stackq.file_util import get_meta_markdown_pairs

headers_to_split_on = [
    ("#", "Header_1"),
    ("##", "Header_2"),
    ("###", "Header_3"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

# Define the Child Splitter (sub-splits parent sections if they are too long)
child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,          # ~100-150 words for precise vector matching
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)

def embed(text: str, hierarchy: list) -> list[float]:
    return ollama.embed(model=EMBED_MODEL, input=f"search_document: {' > '.join(hierarchy)}\n{text}")['embeddings'][0]

def index_and_store_doc(conn, url: str, title: str, category: str, clean_markdown):
    print(f"Index and store \"{title}\"", end=" ...")
    # .../products/security/kms/how-tos/create-and-manage-keys/ -> ["security", "kms", "how-tos"]
    product_path = urlparse(url).path.strip("/").split("/")[1:-1]
    with conn.cursor() as cur:
        # Re-indexing: drop the old page first; ON DELETE CASCADE removes its chunks
        cur.execute("DELETE FROM stackq_pages WHERE url = %s;", (url,))

        page_id = insert_page(cur, url, title, category)

        # Structural Split (Creates Parent Sections)
        parent_docs = markdown_splitter.split_text(clean_markdown)

        for p_doc in parent_docs:
            parent_text = p_doc.page_content.strip()
            if not parent_text:
                continue
            # Extract header hierarchy from metadata dict
            hierarchy = [p_doc.metadata.get(h) for _, h in headers_to_split_on if h in p_doc.metadata]
            # Use title if empty
            hierarchy = [title, *hierarchy]

            # Save Parent Chunk (No embedding needed for the parent itself)
            parent_id = insert_chunk_parent(cur, page_id, parent_text, hierarchy)

            # Sub-split into Child Chunks
            child_docs = child_splitter.split_text(parent_text)

            for child_text in child_docs:
                child_text = child_text.strip()
                if not child_text:
                    continue

                child_embedding = embed(child_text, [*product_path, *hierarchy])

                # Save Child Chunk (Linked to Parent ID)
                insert_chunk(cursor=cur, page_id=page_id, parent_id=parent_id, content=child_text, hierarchy=hierarchy, embedding=child_embedding)
    conn.commit()
    print("Done")

def index_and_store(limit: int | None = None):
    conn = connect()
    pairs = get_meta_markdown_pairs()
    if limit is not None:
        pairs = pairs[:limit]
    ok = failed = 0        
    for pair in pairs:
        try: 
            metadata = pair.read_meta()
            index_and_store_doc(conn, metadata.url, metadata.title, metadata.category, pair.read_content())
            ok += 1
        except Exception as e:
            conn.rollback()
            failed += 1
            print(f"Error while chunking {e}")
    print(f"Done: {ok} pages scraped, {failed} failed")
    return ok, failed

if __name__ == "__main__":
    index_and_store(1)

