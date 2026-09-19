from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        """Generate a complete text response given a system prompt and user input."""
        pass

    @abstractmethod
    async def generate_response_stream(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> AsyncIterator[str]:
        """Stream response chunks asynchronously."""
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Compute single text vector embedding."""
        pass

    @abstractmethod
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Compute vector embeddings for a list of texts."""
        pass
