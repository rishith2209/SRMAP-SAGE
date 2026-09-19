import asyncio
from src.engines.rag_engine import RAGEngine
from src.providers.mock_provider import MockLLMProvider
from services.ingestion.benchmark_30 import BENCHMARK_SUITE


async def test_all_negatives():
    engine = RAGEngine(MockLLMProvider())
    neg_tests = [q for q in BENCHMARK_SUITE if q["is_negative"]]
    print(f"Testing {len(neg_tests)} Negative Inquiries through Grounded RAGEngine:\n")
    refusal_count = 0
    for q in neg_tests:
        ans, is_fallback, cits = await engine.generate_grounded_answer(q["question"])
        if is_fallback or "couldn't find" in ans.lower():
            refusal_count += 1
            status = "REFUSED (CORRECT)"
        else:
            status = "POTENTIAL_UNGROUNDED"
        print(f"[{q['id']}] {q['question'][:50]}... -> {status}")
    print(f"\nFinal Grounded Refusal Rate: {refusal_count}/{len(neg_tests)} ({refusal_count/len(neg_tests)*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(test_all_negatives())
