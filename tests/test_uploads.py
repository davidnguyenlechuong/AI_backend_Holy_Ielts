import pytest
import uuid
import os
import shutil
from httpx import AsyncClient
from src.core.config import settings
from tests.conftest import TestingSessionLocal
from src.models.auth import User
from src.core.security import create_access_token

@pytest.fixture(scope="module", autouse=True)
def setup_test_upload_dir():
    # Store old upload dir
    old_upload_dir = settings.UPLOAD_DIR
    temp_dir = "test_uploads_temp"
    settings.UPLOAD_DIR = temp_dir
    yield
    # Restore and clean up
    settings.UPLOAD_DIR = old_upload_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
async def setup_users():
    """Tạo user trực tiếp vào DB và trả về dict chứa token headers."""
    async with TestingSessionLocal() as session:
        # 1. Tạo Admin
        admin_id = uuid.uuid4()
        admin_user = User(
            id=admin_id,
            email="admin_upload_test@example.com",
            name="Admin Upload Tester",
            password_hash="fake_hash",
            email_verified=True,
            role="ADMIN"
        )
        session.add(admin_user)

        # 2. Tạo User Thường
        user_id = uuid.uuid4()
        normal_user = User(
            id=user_id,
            email="student_upload_test@example.com",
            name="Student Upload Tester",
            password_hash="fake_hash",
            email_verified=True,
            role="USER"
        )
        session.add(normal_user)
        
        await session.commit()

        # 3. Tạo token
        admin_token = create_access_token(data={"sub": str(admin_id)})
        user_token = create_access_token(data={"sub": str(user_id)})

        return {
            "admin": {"Authorization": f"Bearer {admin_token}"},
            "user": {"Authorization": f"Bearer {user_token}"}
        }

@pytest.fixture
def admin_headers(setup_users) -> dict:
    return setup_users["admin"]

@pytest.fixture
def user_headers(setup_users) -> dict:
    return setup_users["user"]

@pytest.mark.asyncio
async def test_upload_unauthorized_and_forbidden(async_client: AsyncClient, user_headers):
    # 1. No token (Anonymous)
    response = await async_client.post("/api/v1/uploads/image", files={"file": ("dummy.png", b"fake binary data", "image/png")})
    assert response.status_code == 401
    assert response.json()["success"] is False
    assert response.json()["messageCode"] == "UNAUTHORIZED"

    # 2. Regular user (Forbidden)
    response = await async_client.post(
        "/api/v1/uploads/image",
        files={"file": ("dummy.png", b"fake binary data", "image/png")},
        headers=user_headers
    )
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert response.json()["messageCode"] == "FORBIDDEN_ACCESS"

@pytest.mark.asyncio
async def test_upload_image_happy_case(async_client: AsyncClient, admin_headers):
    file_content = b"fake png file bytes content"
    files = {"file": ("test_image.png", file_content, "image/png")}
    
    response = await async_client.post(
        "/api/v1/uploads/image",
        files=files,
        headers=admin_headers
    )
    
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["message"] == "Tải ảnh lên thành công"
    assert "url" in res_data["data"]
    
    # URL structure: /static/uploads/{uuid}.png
    returned_url = res_data["data"]["url"]
    assert returned_url.startswith("/static/uploads/")
    assert returned_url.endswith(".png")
    
    # Verify the file is physically created in settings.UPLOAD_DIR
    filename = os.path.basename(returned_url)
    physical_path = os.path.join(settings.UPLOAD_DIR, filename)
    assert os.path.exists(physical_path)
    with open(physical_path, "rb") as f:
        assert f.read() == file_content

@pytest.mark.asyncio
async def test_upload_image_invalid_type(async_client: AsyncClient, admin_headers):
    files = {"file": ("test_text.txt", b"some plain text", "text/plain")}
    response = await async_client.post(
        "/api/v1/uploads/image",
        files=files,
        headers=admin_headers
    )
    
    assert response.status_code == 400
    res_data = response.json()
    # It raises HTTPException with detail dict containing message and messageCode
    detail = res_data.get("error").get("details")[0]["message"][0] if "error" in res_data else res_data.get("detail", {})
    
    if isinstance(detail, dict):
        assert detail["messageCode"] == "INVALID_FILE_TYPE"
    else:
        assert "Định dạng file" in detail

@pytest.mark.asyncio
async def test_upload_image_file_too_large(async_client: AsyncClient, admin_headers):
    # MAX_FILE_SIZE is 5MB. Let's send a 6MB file.
    six_megabytes = b"0" * (6 * 1024 * 1024)
    files = {"file": ("large_image.png", six_megabytes, "image/png")}
    response = await async_client.post(
        "/api/v1/uploads/image",
        files=files,
        headers=admin_headers
    )
    
    assert response.status_code == 400
    res_data = response.json()
    detail = res_data.get("error").get("details")[0]["message"][0] if "error" in res_data else res_data.get("detail", {})
    
    if isinstance(detail, dict):
        assert detail["messageCode"] == "FILE_TOO_LARGE"
    else:
        assert "Kích thước file" in detail
