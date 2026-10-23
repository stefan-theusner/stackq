"""Stage 2: split page text into overlapping chunks."""


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    """Split text into chunks of roughly `size` characters with `overlap`."""
    if size <= overlap:
        raise ValueError("size must be larger than overlap")
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += size - overlap
    return chunks
