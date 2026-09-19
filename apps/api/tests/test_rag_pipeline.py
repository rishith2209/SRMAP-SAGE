import pytest
from src.engines.rag_engine import RAGEngine
from src.providers.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_rag_retrieves_attendance_policy():
    provider = MockLLMProvider()
    engine = RAGEngine(provider, catalog_path="data/knowledge_catalog.json")

    chunks = engine.retrieve_chunks("What is the minimum attendance requirement for semester exams?")
    assert len(chunks) > 0
    top_text, top_citation = chunks[0]
    assert "Attendance" in top_citation.title or "Student" in top_citation.title
    assert top_citation.authority_level == 1
    assert top_citation.page_number in [1, 2]


@pytest.mark.asyncio
async def test_rag_retrieves_od_policy():
    provider = MockLLMProvider()
    engine = RAGEngine(provider, catalog_path="data/knowledge_catalog.json")

    chunks = engine.retrieve_chunks("What is the maximum on-duty allowance?")
    assert len(chunks) > 0
    top_text, top_citation = chunks[0]
    assert "On-Duty" in top_citation.title or "OD" in top_citation.title


@pytest.mark.asyncio
async def test_rag_unverified_fallback():
    provider = MockLLMProvider()
    engine = RAGEngine(provider, catalog_path="data/knowledge_catalog.json")

    chunks = engine.retrieve_chunks("What is the flight schedule from London to Mars?")
    assert len(chunks) == 0

    answer, is_fallback, citations = await engine.generate_grounded_answer("What is the flight schedule from London to Mars?")
    assert is_fallback is True
    assert "I couldn't find a reliable official SRMAP source" in answer
    assert len(citations) == 0
