import logging
from src.core.config import settings
from src.providers.base_provider import BaseLLMProvider
from src.providers.gemini_provider import GeminiLLMProvider
from src.providers.mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> BaseLLMProvider:
    provider_type = settings.LLM_PROVIDER.lower()

    if provider_type == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is empty. Falling back to MockLLMProvider for offline safe mode.")
            return MockLLMProvider()
        return GeminiLLMProvider()
    elif provider_type == "mock":
        return MockLLMProvider()
    else:
        logger.warning(f"Unsupported or unconfigured provider: {provider_type}. Using MockLLMProvider.")
        return MockLLMProvider()
