from src.ai.providers.base import BaseAIProvider
from src.ai.providers.openai import OpenAIProvider
from src.ai.providers.gemini import GeminiProvider
from src.ai.providers.claude import ClaudeProvider

class AIProviderFactory:
    """
    Factory để lấy đối tượng AI Provider tương ứng.
    Mặc định trả về OpenAIProvider.
    """
    
    @staticmethod
    def get_provider(provider_type: str = "openai") -> BaseAIProvider:
        provider_type = provider_type.lower()
        
        if provider_type == "openai":
            return OpenAIProvider()
        elif provider_type == "gemini":
            return GeminiProvider()
        elif provider_type == "claude":
            return ClaudeProvider()
        else:
            raise ValueError(f"AI Provider '{provider_type}' is not supported.")
