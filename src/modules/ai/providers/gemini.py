import os
from google import genai
from google.genai import types
from fastapi import HTTPException
from typing import AsyncIterator, Optional
from src.modules.ai.providers.base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    """
    Provider triển khai việc gọi API tới Google Gemini sử dụng SDK google-genai mới.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=180_000))
        self.default_model = "gemini-3.5-flash"

    def _build_contents(self, user_prompt: str, image_bytes: Optional[bytes], mime_type: Optional[str], audio_bytes: Optional[bytes], audio_mime_type: Optional[str]):
        if image_bytes and mime_type:
            return [
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                user_prompt
            ]
        if audio_bytes and audio_mime_type:
            return [
                types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime_type),
                user_prompt
            ]
        return user_prompt

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> str:
        selected_model = model or self.default_model

        try:
            contents = self._build_contents(user_prompt, image_bytes, mime_type, audio_bytes, audio_mime_type)

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

    async def generate_text_stream(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> AsyncIterator[str]:
        selected_model = model or self.default_model

        try:
            contents = self._build_contents(user_prompt, image_bytes, mime_type, audio_bytes, audio_mime_type)

            stream = await self.client.aio.models.generate_content_stream(
                model=selected_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                )
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini AI Error: {str(e)}")
