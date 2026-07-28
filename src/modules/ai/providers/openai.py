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

    # Các model chỉ chấp nhận temperature mặc định (=1), không hỗ trợ tùy chỉnh
    FIXED_TEMPERATURE_MODELS = ("gpt-5.6-terra",)

    # Model gpt-5.6-terra chỉ nhận content dạng "text"/"image_url", KHÔNG hỗ trợ
    # "input_audio" (trả lỗi 400 "Content blocks are expected to be either text or
    # image_url type"). Khi có audio, bắt buộc phải chuyển sang model hỗ trợ audio input.
    AUDIO_INPUT_MODEL = "gpt-4o-transcribe"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.default_model = "gpt-5.6-terra"

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> str:
        selected_model = self.AUDIO_INPUT_MODEL if audio_bytes else (model or self.default_model)

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
            elif audio_bytes and audio_mime_type:
                base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
                # OpenAI GPT-4o Audio API structure (format must be "wav" or "mp3")
                # Using general "wav" if mime_type contains wav, else "mp3"
                audio_format = "wav" if "wav" in audio_mime_type.lower() else "mp3"
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": base64_audio,
                                "format": audio_format
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": user_prompt})

            request_kwargs = {"model": selected_model, "messages": messages}
            if selected_model not in self.FIXED_TEMPERATURE_MODELS:
                request_kwargs["temperature"] = temperature
            if selected_model == self.AUDIO_INPUT_MODEL:
                # Bắt buộc chỉ định modalities=["text"] để model CHỈ trả về text,
                # không trả kèm audio (nếu không chỉ định, model có thể trả audio
                # khiến message.content bị rỗng và câu trả lời nằm trong message.audio.transcript).
                request_kwargs["modalities"] = ["text"]

            response = await self.client.chat.completions.create(**request_kwargs)
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI Evaluation Error: {str(e)}")
