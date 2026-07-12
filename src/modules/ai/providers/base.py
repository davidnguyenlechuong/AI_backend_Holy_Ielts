from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    """
    Abstract Base Class cho tất cả các AI Providers (OpenAI, Gemini, Claude...).
    Mọi Provider mới được thêm vào hệ thống đều phải kế thừa class này và implement các method bắt buộc.
    """

    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None) -> str:
        """
        Gửi request sinh text (chat completion) tới AI.
        
        Args:
            system_prompt: Lời chỉ dẫn (vai trò) cho AI.
            user_prompt: Nội dung cần AI xử lý.
            temperature: Độ sáng tạo của câu trả lời.
            model: Tên model cụ thể (nếu None sẽ dùng model mặc định của provider).
            
        Returns:
            Text do AI sinh ra.
        """
        pass
