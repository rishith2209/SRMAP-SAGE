import logging
from typing import List, AsyncIterator
from src.providers.base_provider import BaseLLMProvider
from src.core.config import settings

logger = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini provider utilizing the official Google GenAI SDK.
    Optimized for fast inference and long-context RAG.
    """

    def __init__(self, api_key: str = "", model: str = "", embedding_model: str = ""):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self.embedding_model_name = embedding_model or settings.GEMINI_EMBEDDING_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not configured.")
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self._client = legacy_genai
        return self._client

    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        client = self._get_client()
        try:
            from google import genai
            from google.genai import types
            if isinstance(client, genai.Client):
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                return response.text or ""
        except (ImportError, AttributeError):
            pass

        # Fallback to google.generativeai
        import google.generativeai as legacy_genai
        model = legacy_genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )
        response = await model.generate_content_async(
            prompt,
            generation_config=legacy_genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        return response.text or ""

    async def generate_response_stream(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> AsyncIterator[str]:
        client = self._get_client()
        try:
            from google import genai
            from google.genai import types
            if isinstance(client, genai.Client):
                response_stream = client.models.generate_content_stream(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                return
        except (ImportError, AttributeError):
            pass

        # Fallback
        import google.generativeai as legacy_genai
        model = legacy_genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )
        response = await model.generate_content_async(
            prompt,
            stream=True,
            generation_config=legacy_genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def generate_embedding(self, text: str) -> List[float]:
        results = await self.generate_embeddings_batch([text])
        return results[0] if results else []

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        client = self._get_client()
        try:
            from google import genai
            if isinstance(client, genai.Client):
                resp = client.models.embed_content(
                    model=self.embedding_model_name,
                    contents=texts
                )
                return [embedding.values for embedding in resp.embeddings]
        except (ImportError, AttributeError):
            pass

        import google.generativeai as legacy_genai
        result = legacy_genai.embed_content(
            model=f"models/{self.embedding_model_name}",
            content=texts,
            task_type="retrieval_document"
        )
        return result['embedding']
