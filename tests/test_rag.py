import pytest
from src.core.rag_engine import RAGEngine


def test_rag_generation_empty_chunks():
    engine = RAGEngine()
    result = engine.generate("Any flights available?", retrieved_chunks=[])
    assert "No relevant travel documentation" in result["answer"]
    assert result["citations"] == []


def test_rag_generation_mock_synthesis():
    engine = RAGEngine()
    mock_chunks = [
        {
            "id": "mock-1",
            "title": "Swiss Rail Pass",
            "content": "Glacier express connects Zermatt to St Moritz.",
            "location": "Switzerland",
            "source_url": "https://swiss.travel/guide.pdf"
        }
    ]
    result = engine.generate("Tell me about Swiss rail", retrieved_chunks=mock_chunks)
    assert len(result["citations"]) == 1
    assert result["citations"][0]["title"] == "Swiss Rail Pass"
    assert result["latency_seconds"] >= 0
