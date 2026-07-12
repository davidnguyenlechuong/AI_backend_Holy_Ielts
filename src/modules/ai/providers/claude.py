import os
import base64
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from typing import Optional
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

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None) -> str:
        selected_model = model or self.default_model
        try:
            if image_bytes and mime_type:
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": base64_image,
                        }
                    },
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            else:
                content = user_prompt

            response = await self.client.messages.create(
                model=selected_model,
                max_tokens=4096,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            return response.content[0].text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Claude AI Error: {str(e)}")
