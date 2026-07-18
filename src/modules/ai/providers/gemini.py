import os
from google import genai
from google.genai import types
from fastapi import HTTPException
from typing import Optional
from src.modules.ai.providers.base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    """
    Provider triển khai việc gọi API tới Google Gemini sử dụng SDK google-genai mới.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.default_model = "gemini-3.5-flash"

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> str:
        selected_model = model or self.default_model
        
        try:
            if image_bytes and mime_type:
                contents = [
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    user_prompt
                ]
            elif audio_bytes and audio_mime_type:
                contents = [
                    types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime_type),
                    user_prompt
                ]
            else:
                contents = user_prompt

            # Dùng .aio cho gọi async
            response = await self.client.aio.models.generate_content(
                model=selected_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                )
            )
            return response.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini AI Error: {str(e)}")
