from stackq.chunker import chunk_text


def test_chunks_overlap():
    chunks = chunk_text("a" * 2000, size=800, overlap=150)
    assert len(chunks) == 3
    assert all(len(c) <= 800 for c in chunks)
