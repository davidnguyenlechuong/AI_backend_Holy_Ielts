import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select, func

from tests.conftest import TestingSessionLocal
from src.db.seed import seed_ielts_library
from src.models.ielts import Exam, Tag, Topic, ExamAttempt

@pytest.fixture
async def seed_db():
    async with TestingSessionLocal() as session:
        await seed_ielts_library(session)

@pytest.mark.asyncio
async def test_seed_and_idempotency():
    async with TestingSessionLocal() as session:
        # First seeding
        await seed_ielts_library(session)
        
        # Verify counts
        res = await session.execute(select(func.count(Exam.id)))
        exam_count = res.scalar()
        assert exam_count == 11
        
        res = await session.execute(select(func.count(Tag.id)))
        tag_count = res.scalar()
        assert tag_count > 0
        
        # Second seeding to test idempotency
        await seed_ielts_library(session)
        res = await session.execute(select(func.count(Exam.id)))
        assert res.scalar() == 11

@pytest.mark.asyncio
async def test_get_exams(async_client: AsyncClient, seed_db):
    # Test required skill param
    response = await async_client.get("/api/v1/library/exams")
    assert response.status_code == 422 # missing skill param
    
    # Test valid skill param
    response = await async_client.get("/api/v1/library/exams?skill=WRITING")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0 # should return writing exams
    
    # Verify title parse
    first_exam = data["data"][0]
    assert isinstance(first_exam["title"], dict)
    assert "vi" in first_exam["title"]
    assert "en" in first_exam["title"]
    
    # Test filter by difficulty
    response = await async_client.get("/api/v1/library/exams?skill=WRITING&difficulty=HARD")
    assert response.status_code == 200
    data = response.json()
    for exam in data["data"]:
        assert exam["difficulty"] == "HARD"

    # Test search query
    response = await async_client.get("/api/v1/library/exams?skill=WRITING&search=Renewable")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert "Renewable" in data["data"][0]["title"]["en"]

@pytest.mark.asyncio
async def test_get_exam_detail(async_client: AsyncClient, seed_db):
    # Fetch list to get an ID
    response = await async_client.get("/api/v1/library/exams?skill=WRITING")
    exams_data = response.json()["data"]
    exam_id = exams_data[0]["id"]
    
    response = await async_client.get(f"/api/v1/library/exams/{exam_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == exam_id
    assert len(data["data"]["questions"]) > 0

@pytest.mark.asyncio
async def test_start_attempt(async_client: AsyncClient, seed_db):
    # Register/Login user to get authenticated
    reg_response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "attempt_tester@example.com", "password": "password123", "name": "Attempt Tester"}
    )
    assert reg_response.status_code == 200
    token = reg_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Fetch an exam ID
    response = await async_client.get("/api/v1/library/exams?skill=WRITING")
    exams_data = response.json()["data"]
    exam_id = exams_data[0]["id"]
    
    # Start attempt
    attempt_resp = await async_client.post(
        f"/api/v1/library/exams/{exam_id}/attempts",
        headers=headers
    )
    assert attempt_resp.status_code == 200
    data = attempt_resp.json()
    assert data["success"] is True
    assert "attempt_id" in data["data"]
    assert data["data"]["exam_id"] == exam_id
    assert data["data"]["status"] == "IN_PROGRESS"
    
    # Verify is_completed and attempt_count in exams list
    list_resp = await async_client.get("/api/v1/library/exams?skill=WRITING", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()["data"]
    target_exam = next(e for e in list_data if e["id"] == exam_id)
    assert target_exam["is_completed"] is True
    assert target_exam["attempt_count"] == 1

@pytest.mark.asyncio
async def test_get_tags(async_client: AsyncClient, seed_db):
    response = await async_client.get("/api/v1/library/tags?skill=WRITING")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    for tag in data["data"]:
        assert tag["skill"] == "WRITING"
