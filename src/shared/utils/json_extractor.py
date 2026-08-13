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


_STRING_LITERAL = r'"(?:[^"\\]|\\.)*"'
# "key": "val1", "val2", "val3"  -> AI đôi khi viết field dạng nhiều chuỗi rời rạc
# nối bằng dấu phẩy thay vì 1 chuỗi duy nhất. Nhận diện: sau chuỗi đầu tiên, có
# ít nhất 1 chuỗi khác theo sau bởi dấu phẩy, mà chuỗi đó KHÔNG phải là một key mới
# (key mới sẽ có dấu ':' ngay sau nó).
_MULTI_STRING_FIELD_PATTERN = re.compile(
    r'"(?P<key>(?:[^"\\]|\\.)*)"\s*:\s*'
    rf'{_STRING_LITERAL}'
    rf'(?:\s*,\s*{_STRING_LITERAL}(?!\s*:))+'
)
_STRING_LITERAL_PATTERN = re.compile(_STRING_LITERAL)


def _fix_multi_string_fields(text: str) -> str:
    """
    Tự động sửa field dạng "key": "câu 1", "câu 2", "câu 3" (không hợp lệ JSON vì
    thiếu ngoặc vuông bao ngoài) thành "key": "câu 1, câu 2, câu 3" (1 chuỗi duy nhất).
    """
    def _join_match(match: "re.Match[str]") -> str:
        key = match.group("key")
        value_part = match.group(0).split(":", 1)[1]
        # Mỗi match đã bao gồm dấu ngoặc kép bao quanh -> bỏ ngoặc đầu/cuối để lấy nội dung.
        literals = _STRING_LITERAL_PATTERN.findall(value_part)
        values = [literal[1:-1] for literal in literals]
        joined = ", ".join(v.strip() for v in values if v.strip())
        return f'"{key}": "{joined}"'

    return _MULTI_STRING_FIELD_PATTERN.sub(_join_match, text)


def parse_ai_json_response(raw_response: str) -> dict[str, Any]:
    """
    Parse JSON object từ raw text trả về bởi AI provider.
    Tự động loại bỏ markdown code fence, bỏ qua text thừa trước/sau JSON,
    và cố gắng sửa các lỗi JSON phổ biến do LLM sinh ra (newline chưa escape,
    dấu phẩy dư...). Raise ValueError với message rõ ràng nếu vẫn không parse
    được, kèm log lại nguyên văn response thô để debug.
    """
    # In/log nguyên văn raw response TRƯỚC KHI áp dụng bất kỳ xử lý nào.
    try:
        print(f"[AI RAW RESPONSE - BEFORE PARSING]\n{raw_response}\n[END AI RAW RESPONSE]", flush=True)
    except UnicodeEncodeError:
        # Console encoding (e.g. cp1252 on Windows) can't represent some characters (Vietnamese, etc.) - don't let a debug print crash the request.
        pass
    logger.info("Raw AI response (before parsing):\n%s", raw_response)

    if not raw_response or not raw_response.strip():
        raise ValueError("AI response rỗng, không có nội dung để parse JSON.")

    cleaned = _strip_code_fence_markers(raw_response)
    candidate = _extract_outer_json_block(cleaned) or cleaned
    # Sửa trước các field dạng "key": "câu 1", "câu 2" (nhiều chuỗi rời rạc không có
    # ngoặc vuông bao ngoài) -> nối thành 1 chuỗi duy nhất, để json.loads() parse được.
    candidate = _fix_multi_string_fields(candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # strict=False: cho phép ký tự control (ví dụ newline literal) nằm trong string value,
    # lỗi rất phổ biến khi LLM sinh JSON có "comment"/"overall_feedback" nhiều dòng.
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
