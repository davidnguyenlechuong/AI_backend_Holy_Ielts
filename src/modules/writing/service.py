import os
from fastapi import HTTPException
from src.modules.ai.factory import AIProviderFactory
from src.shared.utils.json_extractor import parse_ai_json_response
from pathlib import Path
from typing import Optional

PROMPT_DIR = Path("src/modules/ai/prompts")

async def evaluate_task1(
    topic: str, 
    essay: str, 
    image_bytes: bytes,
    mime_type: str,
    target_band: float = 0.0,
    feedback_language: str = "vi"
) -> dict:
    prompt_path = PROMPT_DIR / "writing_eval_task1.md"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Prompt file not found: writing_eval_task1.md")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)
    
    system_prompt = "You are a helpful and expert IELTS examiner."
    user_prompt = prompt_template.replace("{topic}", topic)\
                                 .replace("{essay}", essay)\
                                 .replace("{target_band}", str(target_band))\
                                 .replace("{feedback_language}", feedback_language)

    try:
        response_text = await ai_provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_bytes=image_bytes,
            mime_type=mime_type
        )
    except Exception as e:
        print(f">>> LOI GOI AI PROVIDER (TASK1): {repr(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")

    print(">>> RAW AI RESPONSE (TASK1):", repr(response_text), flush=True)

    try:
        return parse_ai_json_response(response_text)
    except ValueError as e:
        print(f">>> LOI PARSE JSON (TASK1): {repr(e)}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))

async def evaluate_task2(
    topic: str, 
    essay: str,
    target_band: float = 0.0,
    feedback_language: str = "vi"
) -> dict:
    print(">>> BAT DAU XU LY REQUEST", flush=True)

    prompt_path = PROMPT_DIR / "writing_eval_task2.md"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Prompt file not found: writing_eval_task2.md")

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    print(f">>> AI_PROVIDER_TYPE: {provider_type}", flush=True)
    ai_provider = AIProviderFactory.get_provider(provider_type)

    system_prompt = "You are a helpful and expert IELTS examiner."
    user_prompt = prompt_template.replace("{topic}", topic)\
                                 .replace("{essay}", essay)\
                                 .replace("{target_band}", str(target_band))\
                                 .replace("{feedback_language}", feedback_language)

    try:
        response_text = await ai_provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
    except Exception as e:
        print(f">>> LOI GOI AI PROVIDER: {repr(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")

    print(">>> RAW AI RESPONSE:", repr(response_text), flush=True)

    try:
        return parse_ai_json_response(response_text)
    except ValueError as e:
        print(f">>> LOI PARSE JSON: {repr(e)}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
