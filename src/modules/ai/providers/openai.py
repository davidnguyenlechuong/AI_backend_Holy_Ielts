import os
import base64
from openai import AsyncOpenAI
from fastapi import HTTPException
from typing import Optional
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
        self.default_model = "gpt-4o"

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None) -> str:
        selected_model = model or self.default_model
        
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if image_bytes and mime_type:
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": user_prompt})

            response = await self.client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI Evaluation Error: {str(e)}")
