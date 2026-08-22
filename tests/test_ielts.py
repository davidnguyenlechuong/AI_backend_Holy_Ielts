import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select, func

from tests.conftest import TestingSessionLocal
from src.models.auth import User
from src.models.ielts import IeltsQuestion, IeltsExam, IeltsExamQuestion, IeltsAttempt
from src.core.security import create_access_token

@pytest.fixture
async def setup_users():
    """Tạo user trực tiếp vào DB và trả về dict chứa token headers."""
    async with TestingSessionLocal() as session:
        # 1. Tạo Admin
        admin_id = uuid.uuid4()
        admin_user = User(
            id=admin_id,
            email="admin_test@example.com",
            name="Testing Admin",
            password_hash="fake_hash",
            email_verified=True,
            role="ADMIN"
        )
        session.add(admin_user)

        # 2. Tạo User Thường
        user_id = uuid.uuid4()
        normal_user = User(
            id=user_id,
            email="student_test@example.com",
            name="Testing Student",
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
async def test_admin_unauthorized_and_forbidden(async_client: AsyncClient, user_headers):
    response = await async_client.get("/api/v1/admin/tests")
    assert response.status_code == 401
    assert response.json()["success"] is False
    assert response.json()["messageCode"] == "UNAUTHORIZED"

    response = await async_client.get("/api/v1/admin/tests", headers=user_headers)
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert response.json()["messageCode"] == "FORBIDDEN_ACCESS"


@pytest.mark.asyncio
async def test_admin_question_crud(async_client: AsyncClient, admin_headers):
    payload = {
        "skill": "WRITING",
        "part": "TASK_1",
        "questionType": "bar_chart",
        "topic": "Verify bar chart details.",
        "imageUrl": "https://example.com/bar.png",
        "bulletPoints": None
    }
    response = await async_client.post("/api/v1/admin/tests", json=payload, headers=admin_headers)
    assert response.status_code == 201
    question_data = response.json()["data"]
    
    # Check key linh hoạt theo camelCase hoặc snake_case
    q_type = question_data.get("questionType") or question_data.get("question_type")
    q_image = question_data.get("imageUrl") or question_data.get("image_url")

    assert question_data["skill"] == "WRITING"
    assert question_data["part"] == "TASK_1"
    assert q_type == "bar_chart"
    assert question_data["topic"] == "Verify bar chart details."
    question_id = question_data["id"]

    # 2. Create invalid Question Type (Expect 422)
    invalid_payload = {**payload, "questionType": "agree_disagree"}
    response = await async_client.post("/api/v1/admin/tests", json=invalid_payload, headers=admin_headers)
    assert response.status_code == 422

    # 3. Read (List) with filters
    response = await async_client.get(
        "/api/v1/admin/tests?skill=WRITING&part=TASK_1&questionType=bar_chart",
        headers=admin_headers
    )
    assert response.status_code == 200
    list_data = response.json()["data"]
    assert list_data["total"] >= 1
    assert list_data["items"][0]["id"] == question_id

    # 4. Update (PUT)
    update_payload = {
        "skill": "WRITING",
        "part": "TASK_1",
        "questionType": "line_graph",
        "topic": "Updated Topic details.",
        "imageUrl": None,
        "bulletPoints": None
    }
    response = await async_client.put(
        f"/api/v1/admin/tests/{question_id}",
        json=update_payload,
        headers=admin_headers
    )
    assert response.status_code == 200
    updated_data = response.json()["data"]
    up_type = updated_data.get("questionType") or updated_data.get("question_type")
    assert up_type == "line_graph"
    assert updated_data["topic"] == "Updated Topic details."

    # 5. Delete (DELETE)
    del_resp = await async_client.delete(f"/api/v1/admin/tests/{question_id}", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 6. Verify Deleted 404 on update
    response = await async_client.put(
        f"/api/v1/admin/tests/{question_id}",
        json=update_payload,
        headers=admin_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_exam_crud(async_client: AsyncClient, admin_headers):
    # 1. Create two test questions first
    q1 = (await async_client.post("/api/v1/admin/tests", json={
        "skill": "WRITING", "part": "TASK_1", "questionType": "line_graph",
        "topic": "Line Graph Topic", "imageUrl": None, "bulletPoints": None
    }, headers=admin_headers)).json()["data"]
    
    q2 = (await async_client.post("/api/v1/admin/tests", json={
        "skill": "WRITING", "part": "TASK_2", "questionType": "agree_disagree",
        "topic": "Agree/Disagree Topic", "imageUrl": None, "bulletPoints": None
    }, headers=admin_headers)).json()["data"]

    # 2. Create Full Exam (Draft)
    exam_payload = {
        "title": "IELTS Mock Exam #1",
        "description": "Test mock description",
        "isPublished": False,
        "questions": [
            {"questionId": q1["id"], "orderIndex": 1},
            {"questionId": q2["id"], "orderIndex": 2}
        ]
    }
    response = await async_client.post("/api/v1/admin/exams", json=exam_payload, headers=admin_headers)
    assert response.status_code == 201
    exam_data = response.json()["data"]
    
    is_pub = exam_data.get("isPublished") if "isPublished" in exam_data else exam_data.get("is_published")

    assert exam_data["title"] == "IELTS Mock Exam #1"
    assert is_pub is False
    assert len(exam_data["questions"]) == 2
    
    # handle alias key for question inside response
    first_q = exam_data["questions"][0]
    q_obj = first_q.get("question")
    assert q_obj["id"] == q1["id"]
    exam_id = exam_data["id"]

    # 3. List exams (Admin sees it even if unpublished)
    list_resp = await async_client.get("/api/v1/admin/exams", headers=admin_headers)
    assert list_resp.status_code == 200
    assert any(e["id"] == exam_id for e in list_resp.json()["data"]["items"])

    # 4. Update Exam
    update_payload = {
        "title": "IELTS Mock Exam #1 (Updated)",
        "description": "Updated desc",
        "isPublished": True,
        "questions": [
            {"questionId": q2["id"], "orderIndex": 1}
        ]
    }
    response = await async_client.put(f"/api/v1/admin/exams/{exam_id}", json=update_payload, headers=admin_headers)
    assert response.status_code == 200
    updated_data = response.json()["data"]
    assert updated_data["title"] == "IELTS Mock Exam #1 (Updated)"
    
    up_is_pub = updated_data.get("isPublished") if "isPublished" in updated_data else updated_data.get("is_published")
    assert up_is_pub is True
    assert len(updated_data["questions"]) == 1
    
    up_first_q = updated_data["questions"][0]
    up_q_obj = up_first_q.get("question")
    assert up_q_obj["id"] == q2["id"]

    # 5. Delete Exam
    del_resp = await async_client.delete(f"/api/v1/admin/exams/{exam_id}", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


@pytest.mark.asyncio
async def test_student_practice_flow(async_client: AsyncClient, admin_headers, user_headers):
    # 1. Create a published question and a published exam (containing that question)
    q = (await async_client.post("/api/v1/admin/tests", json={
        "skill": "WRITING", "part": "TASK_1", "questionType": "bar_chart",
        "topic": "Bar Chart Topic", "imageUrl": None, "bulletPoints": None
    }, headers=admin_headers)).json()["data"]

    exam = (await async_client.post("/api/v1/admin/exams", json={
        "title": "Published Practice Exam",
        "description": "Desc",
        "isPublished": True,
        "questions": [
            {"questionId": q["id"], "orderIndex": 1}
        ]
    }, headers=admin_headers)).json()["data"]

    # Un-published exam (Draft) to check if hidden from students
    draft_exam = (await async_client.post("/api/v1/admin/exams", json={
        "title": "Unpublished Exam",
        "description": "Draft",
        "isPublished": False,
        "questions": [
            {"questionId": q["id"], "orderIndex": 1}
        ]
    }, headers=admin_headers)).json()["data"]

    # 2. Public Browse (Questions)
    browse_q = await async_client.get("/api/v1/practice/questions?skill=WRITING&part=TASK_1")
    assert browse_q.status_code == 200
    assert any(item["id"] == q["id"] for item in browse_q.json()["data"]["items"])

    # 3. Public Browse (Exams)
    browse_ex = await async_client.get("/api/v1/practice/exams")
    assert browse_ex.status_code == 200
    list_items = browse_ex.json()["data"]["items"]
    assert any(e["id"] == exam["id"] for e in list_items)
    assert all(e["id"] != draft_exam["id"] for e in list_items)

    # 4. Start Attempt on question (requires user auth)
    att_q_resp = await async_client.post(f"/api/v1/practice/questions/{q['id']}/attempt", headers=user_headers)
    assert att_q_resp.status_code == 201
    att_q_data = att_q_resp.json()["data"]
    
    att_q_status = att_q_data.get("status")
    att_q_question_id = att_q_data.get("questionId") or att_q_data.get("question_id")
    att_q_exam_id = att_q_data.get("examId") or att_q_data.get("exam_id")

    assert att_q_status == "IN_PROGRESS"
    assert att_q_question_id == q["id"]
    assert att_q_exam_id is None
    attempt_q_id = att_q_data["id"]

    # 5. Start Attempt on exam
    att_ex_resp = await async_client.post(f"/api/v1/practice/exams/{exam['id']}/attempt", headers=user_headers)
    assert att_ex_resp.status_code == 201
    att_ex_data = att_ex_resp.json()["data"]
    
    att_ex_status = att_ex_data.get("status")
    att_ex_question_id = att_ex_data.get("questionId") or att_ex_data.get("question_id")
    att_ex_exam_id = att_ex_data.get("examId") or att_ex_data.get("exam_id")

    assert att_ex_status == "IN_PROGRESS"
    assert att_ex_question_id is None
    assert att_ex_exam_id == exam["id"]
    attempt_ex_id = att_ex_data["id"]

    # 6. Submit Attempt on single question (with writing text)
    submit_resp = await async_client.put(
        f"/api/v1/practice/attempts/{attempt_q_id}/submit",
        json={"answerText": "This is a dummy student writing answer text.", "audioUrl": None},
        headers=user_headers
    )
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()["data"]
    sub_status = submit_data.get("status")
    sub_at = submit_data.get("submittedAt") or submit_data.get("submitted_at")

    assert sub_status == "SUBMITTED"
    assert sub_at is not None

    # Try submitting again (should raise 400 Bad Request)
    dup_submit = await async_client.put(
        f"/api/v1/practice/attempts/{attempt_q_id}/submit",
        json={"answerText": "New text", "audioUrl": None},
        headers=user_headers
    )
    assert dup_submit.status_code == 400
