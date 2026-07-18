from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from src.modules.writing.router import router as writing_router
from src.modules.speaking.router import router as speaking_router
from src.shared.responses.base import ErrorResponseSchema, ErrorContent, ErrorDetails

# Tự động load các biến môi trường từ file .env
load_dotenv()


app = FastAPI(
    title="IELTS AI API",
    description="Backend API cho ứng dụng luyện thi IELTS bằng AI",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        field = ".".join([str(loc) for loc in err["loc"]])
        details.append(ErrorDetails(field=field, message=err["msg"]))
    
    error_resp = ErrorResponseSchema(
        message="Dữ liệu không hợp lệ",
        messageCode="VALIDATION_ERROR",
        error=ErrorContent(details=details),
        path=request.url.path
    )
    return JSONResponse(status_code=422, content=error_resp.model_dump(mode='json'))

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_resp = ErrorResponseSchema(
        message=str(exc.detail),
        messageCode="HTTP_ERROR",
        error=ErrorContent(details=str(exc.detail)),
        path=request.url.path
    )
    return JSONResponse(status_code=exc.status_code, content=error_resp.model_dump(mode='json'))

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    error_resp = ErrorResponseSchema(
        message="Đã xảy ra lỗi hệ thống",
        messageCode="INTERNAL_SERVER_ERROR",
        error=ErrorContent(details=str(exc)),
        path=request.url.path
    )
    return JSONResponse(status_code=500, content=error_resp.model_dump(mode='json'))

# Cấu hình CORS để frontend có thể gọi được API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routers (không yêu cầu Auth)
app.include_router(writing_router, prefix="/api/v1")
app.include_router(speaking_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to IELTS AI API!"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
