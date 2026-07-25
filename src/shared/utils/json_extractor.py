import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CODE_FENCE_MARKER_PATTERN = re.compile(r"```(?:json)?", re.IGNORECASE)


def _strip_code_fence_markers(text: str) -> str:
    """Xoá toàn bộ dấu ``` / ```json trong text, giữ nguyên phần nội dung còn lại."""
    return _CODE_FENCE_MARKER_PATTERN.sub("", text).strip()


def _extract_outer_json_block(text: str) -> Optional[str]:
    """
    Lấy đúng đoạn JSON object từ dấu '{' ĐẦU TIÊN đến dấu '}' CUỐI CÙNG trong text.
    Cách này đáng tin cậy hơn regex "\\{.*\\}" vì không phụ thuộc vào việc match
    ngoặc lồng nhau (JSON có nhiều object con cho 4 tiêu chí) và không bị cắt sai
    khi text có nhiều cặp ``` khác nhau.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start:end + 1]


def parse_ai_json_response(raw_response: str) -> dict[str, Any]:
    """
    Parse JSON object từ raw text trả về bởi AI provider.
    Tự động loại bỏ markdown code fence, bỏ qua text thừa trước/sau JSON,
    và cố gắng sửa các lỗi JSON phổ biến do LLM sinh ra (newline chưa escape,
    dấu phẩy dư...). Raise ValueError với message rõ ràng nếu vẫn không parse
    được, kèm log lại nguyên văn response thô để debug.
    """
    # In/log nguyên văn raw response TRƯỚC KHI áp dụng bất kỳ xử lý nào.
    print(f"[AI RAW RESPONSE - BEFORE PARSING]\n{raw_response}\n[END AI RAW RESPONSE]", flush=True)
    logger.info("Raw AI response (before parsing):\n%s", raw_response)

    if not raw_response or not raw_response.strip():
        raise ValueError("AI response rỗng, không có nội dung để parse JSON.")

    cleaned = _strip_code_fence_markers(raw_response)
    candidate = _extract_outer_json_block(cleaned) or cleaned

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # strict=False: cho phép ký tự control (ví dụ newline literal) nằm trong string value,
    # lỗi rất phổ biến khi LLM sinh JSON có "assessment"/"evidence" nhiều dòng.
    try:
        return json.loads(candidate, strict=False)
    except json.JSONDecodeError:
        pass

    # Fallback cuối: dùng json_repair (nếu có cài) để sửa các lỗi JSON phổ biến khác
    # (dấu phẩy dư, thiếu ngoặc đóng, quote sai...).
    try:
        from json_repair import repair_json
        repaired = repair_json(candidate)
        return json.loads(repaired, strict=False)
    except ImportError:
        logger.warning("Thư viện json_repair chưa được cài, bỏ qua bước sửa JSON tự động.")
    except json.JSONDecodeError:
        pass

    logger.error("Không thể parse JSON từ AI response sau khi xử lý. Raw response:\n%s", raw_response)
    raise ValueError("AI trả về dữ liệu không đúng định dạng JSON, vui lòng thử lại.")
