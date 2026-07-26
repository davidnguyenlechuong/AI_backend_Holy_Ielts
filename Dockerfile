# Sử dụng base image python-slim để tối ưu dung lượng
# Lưu ý: Trong pyproject.toml của bạn để requires-python = ">=3.14" 
# nhưng bản chính thức của 3.14 chưa ra mắt. Ta dùng 3.12-slim (hoặc 3.13) rất ổn định và nhẹ.
FROM python:3.12-slim

# Thiết lập các biến môi trường môi trường
# PYTHONDONTWRITEBYTECODE: Ngăn Python tạo file .pyc
# PYTHONUNBUFFERED: Đảm bảo log của Python được in ra ngay lập tức
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AI_PROVIDER_TYPE="openai"

# Đặt thư mục làm việc
WORKDIR /app

# Cài đặt uv (Package manager siêu nhanh bằng Rust)
# Dùng uv để cài đặt các package sẽ giúp tối ưu cả tốc độ lẫn dung lượng cache
RUN pip install --no-cache-dir uv

# Sao chép các file quản lý thư viện vào trước
COPY pyproject.toml uv.lock ./

# Dùng uv sync để tạo môi trường ảo (.venv) đồng bộ chính xác với uv.lock
# --frozen: Đảm bảo không thay đổi uv.lock, bắt buộc dùng các version đã lock
# --no-dev: Không cài các thư viện phục vụ môi trường dev (như pytest)
RUN uv sync --frozen --no-dev

# Đưa biến môi trường PATH trỏ vào .venv để container tự động dùng Python và thư viện trong này
ENV PATH="/app/.venv/bin:$PATH"

# Sao chép toàn bộ mã nguồn
COPY src/ ./src/

# Mở cổng mặc định
EXPOSE 8000

# Lệnh chạy ứng dụng FastAPI
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
