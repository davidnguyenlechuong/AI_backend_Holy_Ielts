# IELTS AI Backend API

Đây là hệ thống Backend cung cấp các API để chấm điểm bài thi IELTS Writing sử dụng trí tuệ nhân tạo (AI). Hệ thống áp dụng kiến trúc **Clean Architecture** (dạng Modular) kết hợp với **Factory Pattern** để linh hoạt chuyển đổi giữa nhiều hãng AI khác nhau (OpenAI, Google Gemini, Anthropic Claude).

## 1. Yêu cầu hệ thống (Prerequisites)

- **Python 3.10+**
- **uv** (Package manager siêu tốc cho Python)

## 2. Cài đặt và Khởi tạo dự án (Setup từ đầu)

Nếu bạn vừa tải dự án này về máy hoặc cài đặt trên một máy tính mới, hãy làm theo các bước sau:

**Bước 1: Cài đặt `uv` (Nếu chưa có)**
`uv` là công cụ quản lý package Python siêu nhanh. Mở Terminal (PowerShell) và chạy:
```bash
# Cài đặt uv trên Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Bước 2: Di chuyển vào thư mục dự án**
```bash
cd d:/Personal/Ielts/ai
```

**Bước 3: Khởi tạo và cài đặt thư viện tự động (uv sync)**
Dự án này đã được cấu hình chuẩn theo `pyproject.toml` của `uv`. Bạn chỉ cần gõ đúng 1 lệnh duy nhất sau đây, `uv` sẽ tự động tạo môi trường ảo (`.venv`) và đồng bộ (tải về) toàn bộ thư viện cần thiết trong nháy mắt:
```bash
uv sync
```

**Bước 4: Cấu hình biến môi trường**
Tạo một file có tên `.env` ở thư mục gốc (cùng cấp với `src`) và điền các API Key của bạn vào:

```env
# Chọn AI Provider sẽ sử dụng: 'openai', 'gemini', hoặc 'claude'
AI_PROVIDER_TYPE=gemini

# Điền các API Key tương ứng
OPENAI_API_KEY=sk-proj-xxxx
GEMINI_API_KEY=AIzaSyxxxx
ANTHROPIC_API_KEY=sk-ant-xxxx
```

## 3. Khởi chạy Server

Sử dụng `uv` để chạy server FastAPI:

```bash
uv run uvicorn src.main:app --reload
```

*Server sẽ chạy ở địa chỉ: `http://127.0.0.1:8000`*

- **Trang Tài liệu Swagger UI:** `http://127.0.0.1:8000/docs`
- **Giao diện test nhanh:** Mở file `frontend_test.html` trực tiếp trên trình duyệt.

## 4. Kiến trúc thư mục (Project Structure)

```text
src/
├── core/                  # (Sắp tới) Chứa các cấu hình lõi: Database, Security, Configs
├── modules/               # Chứa các tính năng chính của hệ thống (Modular)
│   ├── ai/                # Module Quản lý AI (Trái tim của hệ thống)
│   │   ├── factory.py     # Nơi quyết định sẽ gọi OpenAI hay Gemini
│   │   ├── prompts/       # Thư mục chứa File Markdown ra lệnh cho AI (Live-reload)
│   │   └── providers/     # Code gọi API trực tiếp của từng hãng (base, openai, gemini, claude)
│   ├── writing/           # Module Xử lý IELTS Writing
│   │   ├── router.py      # Định nghĩa các đường dẫn (Endpoint) /evaluate/task1, /task2
│   │   ├── schemas.py     # Định nghĩa cấu trúc dữ liệu đầu vào (Pydantic Validation)
│   │   └── service.py     # Xử lý logic đọc file prompt và gọi sang Module AI
│   └── (sắp tới: speaking, reading, listening, users)
├── shared/                # Code dùng chung (Tiện ích, Định dạng Data trả về chuẩn)
└── main.py                # Điểm khởi chạy của toàn bộ ứng dụng (FastAPI App)
```

## 5. Hướng dẫn sử dụng API

Hệ thống có 2 API riêng biệt cho 2 dạng bài thi Writing:

### API 1: Chấm biểu đồ (IELTS Writing Task 1)
- **Đường dẫn:** `POST /api/v1/writing/evaluate/task1`
- **Content-Type:** `multipart/form-data`
- **Tham số bắt buộc:**
  - `topic` (text): Yêu cầu đề bài.
  - `essay` (text): Bài làm của học viên.
  - `image` (file): File ảnh chứa biểu đồ (Line, Bar, Pie chart...).

### API 2: Chấm nghị luận (IELTS Writing Task 2)
- **Đường dẫn:** `POST /api/v1/writing/evaluate/task2`
- **Content-Type:** `application/json`
- **Payload:**
```json
{
  "topic": "Some people think that strict punishments...",
  "essay": "Traffic accidents have become a widespread..."
}
```

## 6. Chỉnh sửa Prompt cho AI

Bạn **KHÔNG** cần phải khởi động lại server nếu muốn đổi giọng văn của AI. Chỉ cần mở file tương ứng trong thư mục `src/modules/ai/prompts/`:
- Sửa `writing_eval_task1.md` nếu muốn đổi cách chấm Biểu đồ.
- Sửa `writing_eval_task2.md` nếu muốn đổi cách chấm Nghị luận xã hội.
Mọi thay đổi sẽ có tác dụng ngay lập tức ở lần gọi API tiếp theo!
