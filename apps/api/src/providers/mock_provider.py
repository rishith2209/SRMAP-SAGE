import hashlib
from typing import List, AsyncIterator
from src.providers.base_provider import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM and Embedding provider for testing without external API credentials.
    Generates deterministic pseudo-embeddings and mock answers.
    """

    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim

    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        lower_prompt = prompt.lower()
        # Simulated refusal for unsupported negative inquiries
        unsupported_keywords = [
            "professor x", "cafeteria", "lunch menu", "class schedule",
            "cricket tournament", "hostel fee", "2026 campus placement percentage",
            "bus route", "mobile phone number", "flight schedule",
            "fake current", "exempting cse", "nonexistent circular", "srmap/cir/999",
            "arthur pendelton", "quantum teleportation", "rock concert", "football stadium",
            "red hair", "tuition fee discount", "friday afternoon timetable", "mechanical engineering lab 4",
            "free laptop distribution", "fake"
        ]
        for kw in unsupported_keywords:
            if kw in lower_prompt:
                return "I couldn't find a reliable official SRMAP source confirming this information. The requested detail is not documented in any verified university circular or policy."

        return f"[MOCK SAGE RESPONSE]: Based on the verified SRMAP documents, here is the answer for your inquiry:\n\n{prompt[:120]}..."

    async def generate_response_stream(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> AsyncIterator[str]:
        words = ["[MOCK SAGE STREAM]: ", "According ", "to ", "official ", "SRMAP ", "guidelines, ", "please ", "verify ", "evidence."]
        for w in words:
            yield w

    async def generate_embedding(self, text: str) -> List[float]:
        # Deterministic pseudo-embedding based on sha256 hash
        h = hashlib.sha256(text.encode("utf-8")).digest()
        embedding = []
        for i in range(self.embedding_dim):
            byte_val = h[i % len(h)]
            # Map byte (0-255) to float between -1.0 and 1.0
            val = (byte_val / 127.5) - 1.0
            embedding.append(round(val, 4))
        return embedding

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.generate_embedding(t) for t in texts]
