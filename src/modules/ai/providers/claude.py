import os
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from src.modules.ai.providers.base import BaseAIProvider

class ClaudeProvider(BaseAIProvider):
    """
    Provider triển khai việc gọi API tới Anthropic Claude.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured.")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.default_model = "claude-3-haiku-20240307"

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None) -> str:
        selected_model = model or self.default_model
        try:
            response = await self.client.messages.create(
                model=selected_model,
                max_tokens=4096,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Claude AI Error: {str(e)}")
