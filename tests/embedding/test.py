import pytest
from src.utils.embedding.text import LocalTextEmbedder

def test_local_text_embedder():
    embedder = LocalTextEmbedder()
    texts = [
        "Hello, world!",
        "Testing text embedding.",
        "This is a sample text for embedding."
    ]
    embeddings = embedder.embed_texts(texts)
    
    assert len(embeddings) == len(texts), "Number of embeddings should match number of texts."
    for embedding in embeddings:
        assert isinstance(embedding, list), "Each embedding should be a list."
        assert all(isinstance(value, float) for value in embedding), "Embedding values should be floats."
        assert len(embedding) == embedder.model.get_sentence_embedding_dimension(), "Embedding dimension should match model's embedding dimension."

