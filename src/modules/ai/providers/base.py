from abc import ABC, abstractmethod
from typing import Optional

class BaseAIProvider(ABC):
    """
    Abstract Base Class cho tất cả các AI Providers (OpenAI, Gemini, Claude...).
    Mọi Provider mới được thêm vào hệ thống đều phải kế thừa class này và implement các method bắt buộc.
    """

    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_mime_type: Optional[str] = None) -> str:
        """
        Gửi request sinh text (chat completion) tới AI.
        
        Args:
            system_prompt: Lời chỉ dẫn (vai trò) cho AI.
            user_prompt: Nội dung cần AI xử lý.
            temperature: Độ sáng tạo của câu trả lời.
            model: Tên model cụ thể (nếu None sẽ dùng model mặc định của provider).
            image_bytes: Dữ liệu ảnh dưới dạng bytes (nếu có).
            mime_type: Định dạng của ảnh (ví dụ: image/jpeg, image/png).
            audio_bytes: Dữ liệu âm thanh dưới dạng bytes (nếu có).
            audio_mime_type: Định dạng âm thanh (ví dụ: audio/mpeg).
            
        Returns:
            Text do AI sinh ra.
        """
        pass
