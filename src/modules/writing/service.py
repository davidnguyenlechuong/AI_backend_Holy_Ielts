import os
from fastapi import HTTPException
from src.modules.ai.factory import AIProviderFactory
from pathlib import Path

PROMPT_DIR = Path("src/modules/ai/prompts")

async def evaluate_writing_essay(topic: str, essay: str) -> str:
    # Đọc nội dung file md trực tiếp mỗi khi gọi API (Giúp live-reload prompt)
    with open(PROMPT_DIR / "writing_eval.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Lấy provider từ Factory (mặc định hoặc cấu hình qua biến môi trường)
    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)
    
    system_prompt = "You are a helpful and expert IELTS examiner."
    
    # Fill dữ liệu thật vào template
    user_prompt = prompt_template.format(topic=topic, essay=essay)
    
    try:
        feedback = await ai_provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7
        )
        return feedback
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI Provider: {str(e)}")
