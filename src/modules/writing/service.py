import os
from fastapi import HTTPException
from src.modules.ai.factory import AIProviderFactory
from pathlib import Path
from typing import Optional

PROMPT_DIR = Path("src/modules/ai/prompts")

async def evaluate_task1(
    topic: str, 
    essay: str, 
    image_bytes: bytes,
    mime_type: str
) -> str:
    prompt_path = PROMPT_DIR / "writing_eval_task1.md"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Prompt file not found: writing_eval_task1.md")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)
    
    system_prompt = "You are a helpful and expert IELTS examiner."
    user_prompt = prompt_template.format(topic=topic, essay=essay)
    
    try:
        return await ai_provider.generate_text(
            system_prompt=system_prompt, 
            user_prompt=user_prompt,
            image_bytes=image_bytes,
            mime_type=mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")

async def evaluate_task2(topic: str, essay: str) -> str:
    prompt_path = PROMPT_DIR / "writing_eval_task2.md"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Prompt file not found: writing_eval_task2.md")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)
    
    system_prompt = "You are a helpful and expert IELTS examiner."
    user_prompt = prompt_template.format(topic=topic, essay=essay)
    
    try:
        return await ai_provider.generate_text(
            system_prompt=system_prompt, 
            user_prompt=user_prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")
