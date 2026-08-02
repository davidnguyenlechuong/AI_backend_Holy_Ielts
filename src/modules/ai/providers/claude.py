import os
import base64
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from typing import AsyncIterator, Optional
from src.modules.ai.providers.base import BaseAIProvider

class ClaudeProvider(BaseAIProvider):
    """
    Provider triển khai việc gọi API tới Anthropic Claude.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured.")

        self.client = AsyncAnthropic(api_key=self.api_key, timeout=180)
        self.default_model = "claude-sonnet-4-6"

    def _build_content(self, user_prompt: str, image_bytes: Optional[bytes], mime_type: Optional[str]):
        if image_bytes and mime_type:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            return [
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
        return user_prompt

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None) -> str:
        selected_model = model or self.default_model
        try:
            content = self._build_content(user_prompt, image_bytes, mime_type)

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

    async def generate_text_stream(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> AsyncIterator[str]:
        selected_model = model or self.default_model
        try:
            content = self._build_content(user_prompt, image_bytes, mime_type)

            async with self.client.messages.stream(
                model=selected_model,
                max_tokens=4096,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Claude AI Error: {str(e)}")
