from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from src.modules.writing.router import router as writing_router
from src.modules.speaking.router import router as speaking_router
from src.modules.auth.router import router as auth_router
from src.modules.payments.router import router as payments_router
from src.modules.users.router import router as users_router
from src.modules.library.router import router as library_router
from src.modules.admin.router import router as admin_router
from src.modules.practice.router import router as practice_router
from src.modules.uploads.router import router as uploads_router
from src.shared.responses.base import ErrorResponseSchema, ErrorContent, ErrorDetails
from src.core.config import settings
from fastapi.staticfiles import StaticFiles
import os

# Tự động load các biến môi trường từ file .env
load_dotenv()


app = FastAPI(
    title="IELTS AI Platform",
    description="Backend API cho ứng dụng luyện thi IELTS bằng AI",
    version="1.0.0"
)

# Đảm bảo thư mục upload tồn tại và mount làm static folder phục vụ upload fallback
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="static_uploads")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        field = ".".join([str(loc) for loc in err["loc"]])
        details.append(ErrorDetails(field=field, message=[err["msg"]]))

    error_resp = ErrorResponseSchema(
        message="Dữ liệu không hợp lệ",
        messageCode="VALIDATION_ERROR",
        error=ErrorContent(details=details),
        path=request.url.path
    )
    return JSONResponse(status_code=422, content=error_resp.model_dump(mode='json'))

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    message = "Đã xảy ra lỗi"
    message_code = "HTTP_ERROR"
    details = []

    if isinstance(detail, dict):
        message = detail.get("message", message)
        message_code = detail.get("messageCode", message_code)
        # Nếu có chi tiết lỗi nhỏ hơn bên trong
        if "error" in detail and detail["error"]:
            details = detail["error"].get("details", [])
        else:
            details = [ErrorDetails(field="server", message=[message])]
    else:
        message = detail
        details = [ErrorDetails(field="server", message=[message])]

    error_resp = ErrorResponseSchema(
        message=message,
        messageCode=message_code,
        error=ErrorContent(details=details) if details else None,
        path=request.url.path
    )
    return JSONResponse(status_code=exc.status_code, content=error_resp.model_dump(mode='json'))


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    error_resp = ErrorResponseSchema(
        message="Đã xảy ra lỗi hệ thống",
        messageCode="INTERNAL_SERVER_ERROR",
        error=ErrorContent(details=[ErrorDetails(field="server", message=[str(exc)])]),
        path=request.url.path
    )
    return JSONResponse(status_code=500, content=error_resp.model_dump(mode='json'))

# Cấu hình CORS để frontend có thể gọi được API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(writing_router, prefix="/api/v1")
app.include_router(speaking_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(library_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(practice_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to IELTS AI API!"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
