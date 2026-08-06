import os
from fastapi import HTTPException
from src.modules.ai.factory import AIProviderFactory
from src.shared.utils.json_extractor import parse_ai_json_response
from pathlib import Path

PROMPT_DIR = Path("src/modules/ai/prompts")


async def _run_speaking_evaluation(
    prompt_file: str,
    placeholder: str,
    value: str,
    audio_bytes: bytes,
    mime_type: str,
    label: str,
    feedback_language: str = "vi",
    max_retries: int = 2,
) -> dict:
    prompt_path = PROMPT_DIR / prompt_file
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail=f"Prompt file not found: {prompt_file}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    provider_type = os.getenv("AI_PROVIDER_TYPE", "openai")
    ai_provider = AIProviderFactory.get_provider(provider_type)

    system_prompt = "You are a helpful and expert IELTS Speaking examiner."
    user_prompt = (
        prompt_template
        .replace(placeholder, value)
        .replace("{feedback_language}", feedback_language)
    )

    REFUSAL_MARKERS = (
        "unable to access", "cannot access", "can't access",
        "unable to process", "cannot process", "can't process",
        "please provide the audio", "provide the audio file",
        "i need to hear", "need to hear the",
        "không thể nghe", "không thể xử lý", "cung cấp bản ghi",
    )

    last_error_detail = "Unknown error"
    for attempt in range(1, max_retries + 2):
        print(f">>> BAT DAU XU LY {label} | PROVIDER: {provider_type} | Lan thu: {attempt}", flush=True)
        try:
            response_text = await ai_provider.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                audio_bytes=audio_bytes,
                audio_mime_type=mime_type
            )
        except Exception as e:
            print(f">>> LOI GOI AI PROVIDER ({label}), lan {attempt}: {repr(e)}", flush=True)
            last_error_detail = str(e)
            continue

        print(f">>> RAW AI RESPONSE ({label}), lan {attempt}:", repr(response_text), flush=True)

        lowered = response_text.lower()
        if any(marker in lowered for marker in REFUSAL_MARKERS):
            print(f">>> MODEL TU CHOI XU LY AUDIO ({label}), se thu lai...", flush=True)
            last_error_detail = "Model refused to process audio"
            continue

        try:
            return parse_ai_json_response(response_text)
        except ValueError as e:
            print(f">>> LOI PARSE JSON ({label}), lan {attempt}: {repr(e)}", flush=True)
            last_error_detail = str(e)
            continue

    raise HTTPException(
        status_code=500,
        detail=f"Lỗi khi gọi AI Provider sau {max_retries + 1} lần thử: {last_error_detail}"
    )


async def evaluate_part1(question: str, audio_bytes: bytes, mime_type: str, feedback_language: str = "vi") -> dict:
    return await _run_speaking_evaluation(
        prompt_file="speaking_eval_part1.md",
        placeholder="{question}",
        value=question,
        audio_bytes=audio_bytes,
        mime_type=mime_type,
        label="SPEAKING PART1",
        feedback_language=feedback_language,
    )


async def evaluate_part2(cue_card: str, audio_bytes: bytes, mime_type: str, feedback_language: str = "vi") -> dict:
    return await _run_speaking_evaluation(
        prompt_file="speaking_eval_part2.md",
        placeholder="{cue_card}",
        value=cue_card,
        audio_bytes=audio_bytes,
        mime_type=mime_type,
        label="SPEAKING PART2",
        feedback_language=feedback_language,
    )


async def evaluate_part3(question: str, audio_bytes: bytes, mime_type: str, feedback_language: str = "vi") -> dict:
    return await _run_speaking_evaluation(
        prompt_file="speaking_eval_part3.md",
        placeholder="{question}",
        value=question,
        audio_bytes=audio_bytes,
        mime_type=mime_type,
        label="SPEAKING PART3",
        feedback_language=feedback_language,
    )