import os
import google.generativeai as genai
from fastapi import HTTPException
from src.modules.ai.providers.base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    """
    Provider triển khai việc gọi API tới Google Gemini.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")
        
        genai.configure(api_key=self.api_key)
        self.default_model = "gemini-1.5-flash"

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None) -> str:
        selected_model = model or self.default_model
        
        try:
            genai_model = genai.GenerativeModel(
                model_name=selected_model,
                system_instruction=system_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                )
            )
            
            response = await genai_model.generate_content_async(user_prompt)
            return response.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini AI Error: {str(e)}")
