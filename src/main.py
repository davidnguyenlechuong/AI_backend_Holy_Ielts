from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

# Tự động load các biến môi trường từ file .env
load_dotenv()

from src.modules.writing.router import router as writing_router

app = FastAPI(
    title="IELTS AI API",
    description="Backend API cho ứng dụng luyện thi IELTS bằng AI",
    version="1.0.0"
)

# Đăng ký router writing (không yêu cầu Auth)
app.include_router(writing_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to IELTS AI API!"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
