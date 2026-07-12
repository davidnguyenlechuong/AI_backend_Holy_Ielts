from src.modules.ai.providers.base import BaseAIProvider
from src.modules.ai.providers.openai import OpenAIProvider
from src.modules.ai.providers.gemini import GeminiProvider
from src.modules.ai.providers.claude import ClaudeProvider

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
