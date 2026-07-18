import os
from fastapi import HTTPException
from src.modules.ai.factory import AIProviderFactory
from pathlib import Path

PROMPT_DIR = Path("src/modules/ai/prompts")

async def evaluate_part1(question: str, audio_bytes: bytes, mime_type: str) -> str:
    prompt_path = PROMPT_DIR / "speaking_eval_part1.md"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Prompt file not found")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)
    
    system_prompt = "You are a helpful and expert IELTS Speaking examiner."
    user_prompt = prompt_template.format(question=question)
    
    try:
        return await ai_provider.generate_text(
            system_prompt=system_prompt, 
            user_prompt=user_prompt,
            audio_bytes=audio_bytes,
            audio_mime_type=mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")

async def evaluate_part2(cue_card: str, audio_bytes: bytes, mime_type: str) -> str:
    prompt_path = PROMPT_DIR / "speaking_eval_part2.md"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Prompt file not found")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)
    
    system_prompt = "You are a helpful and expert IELTS Speaking examiner."
    user_prompt = prompt_template.format(cue_card=cue_card)
    
    try:
        return await ai_provider.generate_text(
            system_prompt=system_prompt, 
            user_prompt=user_prompt,
            audio_bytes=audio_bytes,
            audio_mime_type=mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")

async def evaluate_part3(question: str, audio_bytes: bytes, mime_type: str) -> str:
    prompt_path = PROMPT_DIR / "speaking_eval_part3.md"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Prompt file not found")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)
    
    system_prompt = "You are a helpful and expert IELTS Speaking examiner."
    user_prompt = prompt_template.format(question=question)
    
    try:
        return await ai_provider.generate_text(
            system_prompt=system_prompt, 
            user_prompt=user_prompt,
            audio_bytes=audio_bytes,
            audio_mime_type=mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")
