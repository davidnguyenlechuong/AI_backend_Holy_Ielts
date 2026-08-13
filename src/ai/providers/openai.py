import os
import io
import base64
from openai import AsyncOpenAI
from pydub import AudioSegment
from fastapi import HTTPException
from typing import AsyncIterator, Optional
from src.ai.providers.base import BaseAIProvider
from PIL import Image
import pillow_heif
import pillow_avif

pillow_heif.register_heif_opener()

def _convert_audio_to_wav(audio_bytes: bytes) -> bytes:
    """Convert audio bytes sang WAV thật — OpenAI chat completions chỉ 
    chấp nhận input_audio.format = "wav" hoặc "mp3"."""
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    output = io.BytesIO()
    audio.export(output, format="wav")
    return output.getvalue()

def _convert_image_to_png(image_bytes: bytes) -> bytes:
    """Convert bất kỳ định dạng ảnh nào (AVIF, HEIC, BMP, TIFF...) sang PNG,
    vì OpenAI chỉ chấp nhận png/jpeg/gif/webp."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="File ảnh không hợp lệ hoặc không được hỗ trợ. "
                   "Vui lòng thử tải lên ảnh định dạng khác (PNG/JPEG)."
        )
    
class OpenAIProvider(BaseAIProvider):
    """
    Provider triển khai việc gọi API tới OpenAI.
    """

    # Các model chỉ chấp nhận temperature mặc định (=1), không hỗ trợ tùy chỉnh
    FIXED_TEMPERATURE_MODELS = ("gpt-5.6-terra",)

    # Model gpt-5.6-terra chỉ nhận content dạng "text"/"image_url", KHÔNG hỗ trợ
    # "input_audio" (trả lỗi 400 "Content blocks are expected to be either text or
    # image_url type"). Khi có audio, bắt buộc phải chuyển sang model hỗ trợ audio input.
    AUDIO_INPUT_MODEL = "gpt-audio-mini"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(api_key=self.api_key, timeout=180)
        self.default_model = "gpt-5.6-terra"

    def _build_messages(self, system_prompt: str, user_prompt: str, image_bytes: Optional[bytes], mime_type: Optional[str], audio_bytes: Optional[bytes], audio_mime_type: Optional[str]) -> list:
        messages = [{"role": "system", "content": system_prompt}]

        if image_bytes and mime_type:
            png_bytes = _convert_image_to_png(image_bytes)
            base64_image = base64.b64encode(png_bytes).decode('utf-8')
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            })
        elif audio_bytes and audio_mime_type:
            wav_bytes = _convert_audio_to_wav(audio_bytes)
            base64_audio = base64.b64encode(wav_bytes).decode('utf-8')
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": base64_audio,
                            "format": "wav"
                        }
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": user_prompt})

        return messages

    def _build_request_kwargs(self, selected_model: str, messages: list, temperature: float) -> dict:
        request_kwargs = {"model": selected_model, "messages": messages}
        if selected_model not in self.FIXED_TEMPERATURE_MODELS:
            request_kwargs["temperature"] = temperature
        if selected_model == self.AUDIO_INPUT_MODEL:
            # Bắt buộc chỉ định modalities=["text"] để model CHỈ trả về text,
            # không trả kèm audio (nếu không chỉ định, model có thể trả audio
            # khiến message.content bị rỗng và câu trả lời nằm trong message.audio.transcript).
            request_kwargs["modalities"] = ["text"]
        return request_kwargs

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> str:
        selected_model = self.AUDIO_INPUT_MODEL if audio_bytes else (model or self.default_model)

        try:
            messages = self._build_messages(system_prompt, user_prompt, image_bytes, mime_type, audio_bytes, audio_mime_type)
            request_kwargs = self._build_request_kwargs(selected_model, messages, temperature)

            response = await self.client.chat.completions.create(**request_kwargs)
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI Evaluation Error: {str(e)}")

    async def generate_text_stream(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> AsyncIterator[str]:
        selected_model = self.AUDIO_INPUT_MODEL if audio_bytes else (model or self.default_model)

        try:
            messages = self._build_messages(system_prompt, user_prompt, image_bytes, mime_type, audio_bytes, audio_mime_type)
            request_kwargs = self._build_request_kwargs(selected_model, messages, temperature)
            request_kwargs["stream"] = True

            response = await self.client.chat.completions.create(**request_kwargs)
            async for chunk in response:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI Evaluation Error: {str(e)}")
