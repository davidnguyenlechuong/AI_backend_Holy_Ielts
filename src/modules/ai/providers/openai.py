import os
from openai import AsyncOpenAI
from fastapi import HTTPException
from src.modules.ai.providers.base import BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    """
    Provider triển khai việc gọi API tới OpenAI.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.default_model = "gpt-4o-mini"

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None) -> str:
        selected_model = model or self.default_model
        try:
            response = await self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI Evaluation Error: {str(e)}")
