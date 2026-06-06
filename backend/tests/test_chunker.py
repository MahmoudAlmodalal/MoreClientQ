from app.services.rag.chunker import chunk_text, RecursiveCharacterTextSplitter

def test_recursive_character_text_splitter_basic():
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=2, separators=[" ", ""])
    text = "hello world"
    chunks = splitter.split_text(text)
    assert chunks == ["hello", "world"]

def test_recursive_character_text_splitter_with_overlap():
    splitter = RecursiveCharacterTextSplitter(chunk_size=15, chunk_overlap=5, separators=[" "])
    text = "one two three four"
    chunks = splitter.split_text(text)
    assert chunks == ["one two three", "three four"]

def test_chunk_text_helper():
    text = "This is a simple test document for chunking."
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.text) <= 20
        assert hasattr(chunk, "text")
