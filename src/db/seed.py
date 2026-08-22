import json
import uuid
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from typing import cast, Dict, Any, List
from src.core.config import settings
from src.core.security import get_password_hash
from src.db.base import Base
from src.models.auth import User
from src.models.ielts import Topic, Tag, Exam, ExamQuestion, exam_tags

# Idempotent seed data with fixed UUIDs
TOPIC_IDS = {
    "education": uuid.UUID("01a01a00-0000-7000-a000-000000000001"),
    "environment": uuid.UUID("01a01a00-0000-7000-a000-000000000002"),
    "technology": uuid.UUID("01a01a00-0000-7000-a000-000000000003"),
    "health": uuid.UUID("01a01a00-0000-7000-a000-000000000004"),
    "society": uuid.UUID("01a01a00-0000-7000-a000-000000000005"),
}

async def seed_ielts_library(db: AsyncSession):
    # 1. Seed Topics
    topics_data = [
        {"id": TOPIC_IDS["education"], "name": "Education", "slug": "education", "description": "Topics related to schooling, university, learning, and academic systems."},
        {"id": TOPIC_IDS["environment"], "name": "Environment", "slug": "environment", "description": "Topics related to nature, pollution, climate change, and renewable energy."},
        {"id": TOPIC_IDS["technology"], "name": "Technology", "slug": "technology", "description": "Topics related to computers, internet, AI, and remote work."},
        {"id": TOPIC_IDS["health"], "name": "Health", "slug": "health", "description": "Topics related to healthcare, fitness, diet, and healthcare spending."},
        {"id": TOPIC_IDS["society"], "name": "Society", "slug": "society", "description": "Topics related to population growth, demographics, city planning, and culture."},
    ]
    for topic_info in topics_data:
        res = await db.execute(select(Topic).filter(Topic.id == topic_info["id"]))
        existing = res.scalars().first()
        if not existing:
            new_topic = Topic(**topic_info)
            db.add(new_topic)
    await db.commit()

    # 2. Seed Tags
    tags_data = [
        # Reading
        {"code": "READING_SUMMARY_COMPLETION", "name": {"vi": "Hoàn thành bài tóm tắt", "en": "Summary Completion"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_TRUE_FALSE_NOT_GIVEN", "name": {"vi": "True / False / Not Given", "en": "True / False / Not Given"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MULTIPLE_CHOICE", "name": {"vi": "Trắc nghiệm", "en": "Multiple Choice"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MATCHING_PARAGRAPH_INFO", "name": {"vi": "Nối thông tin đoạn văn", "en": "Matching Paragraph Information"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MATCHING_NAME", "name": {"vi": "Nối tên tác giả/nhân vật", "en": "Matching Name"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_YES_NO_NOT_GIVEN", "name": {"vi": "Yes / No / Not Given", "en": "Yes / No / Not Given"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MATCHING_HEADINGS", "name": {"vi": "Nối tiêu đề đoạn văn", "en": "Matching Headings"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_SENTENCE_COMPLETION", "name": {"vi": "Hoàn thành câu", "en": "Sentence Completion"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_LIST_SELECTION", "name": {"vi": "Lựa chọn từ danh sách", "en": "List Selection"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_SHORT_ANSWER", "name": {"vi": "Trả lời câu hỏi ngắn", "en": "Short Answer"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MATCHING_SENTENCE_ENDINGS", "name": {"vi": "Nối phần cuối của câu", "en": "Matching Sentence Endings"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_TABLE_COMPLETION", "name": {"vi": "Hoàn thành bảng biểu", "en": "Table Completion"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_FLOW_CHART_COMPLETION", "name": {"vi": "Hoàn thành lưu đồ", "en": "Flow Chart Completion"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_DIAGRAM_COMPLETION", "name": {"vi": "Hoàn thành biểu đồ/quy trình", "en": "Diagram Completion"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_CHOOSE_TITLE", "name": {"vi": "Lựa chọn tiêu đề", "en": "Choose a Title"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_NOTE_COMPLETION", "name": {"vi": "Hoàn thành ghi chú", "en": "Note Completion"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MATCHING_FEATURES_NAME", "name": {"vi": "Nối đặc điểm/nhân vật", "en": "Matching Features / Name"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MATCHING_INFORMATION", "name": {"vi": "Nối thông tin chi tiết", "en": "Matching Information"}, "skill": "READING", "category": "READING_Q_TYPE"},
        {"code": "READING_MATCHING_FEATURES", "name": {"vi": "Nối đặc điểm", "en": "Matching Features"}, "skill": "READING", "category": "READING_Q_TYPE"},

        # Listening
        {"code": "LISTENING_MULTIPLE_CHOICE", "name": {"vi": "Trắc nghiệm", "en": "Multiple Choice"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_MULTIPLE_CHOICE_MULTIPLE_ANSWERS", "name": {"vi": "Trắc nghiệm nhiều đáp án", "en": "Multiple Choice — Multiple Answers"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_MATCHING", "name": {"vi": "Nối thông tin", "en": "Matching"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_MAP_LABELLING", "name": {"vi": "Dán nhãn bản đồ", "en": "Map Labelling"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_PLAN_LABELLING", "name": {"vi": "Dán nhãn sơ đồ phòng/khu vực", "en": "Plan Labelling"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_DIAGRAM_LABELLING", "name": {"vi": "Dán nhãn biểu đồ quy trình", "en": "Diagram Labelling"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_FORM_COMPLETION", "name": {"vi": "Hoàn thành biểu mẫu", "en": "Form Completion"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_NOTE_COMPLETION", "name": {"vi": "Hoàn thành ghi chú", "en": "Note Completion"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_TABLE_COMPLETION", "name": {"vi": "Hoàn thành bảng biểu", "en": "Table Completion"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_FLOW_CHART_COMPLETION", "name": {"vi": "Hoàn thành lưu đồ", "en": "Flow Chart Completion"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_SUMMARY_COMPLETION", "name": {"vi": "Hoàn thành bài tóm tắt", "en": "Summary Completion"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_SENTENCE_COMPLETION", "name": {"vi": "Hoàn thành câu", "en": "Sentence Completion"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_SHORT_ANSWER", "name": {"vi": "Trả lời câu hỏi ngắn", "en": "Short Answer"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},
        {"code": "LISTENING_LIST_SELECTION", "name": {"vi": "Lựa chọn từ danh sách", "en": "List Selection"}, "skill": "LISTENING", "category": "LISTENING_Q_TYPE"},

        # Writing Task 1
        {"code": "WRITING_T1_LINE_GRAPH", "name": {"vi": "Biểu đồ đường", "en": "Line Graph"}, "skill": "WRITING", "category": "WRITING_T1_TYPE"},
        {"code": "WRITING_T1_BAR_CHART", "name": {"vi": "Biểu đồ cột", "en": "Bar Chart"}, "skill": "WRITING", "category": "WRITING_T1_TYPE"},
        {"code": "WRITING_T1_PIE_CHART", "name": {"vi": "Biểu đồ tròn", "en": "Pie Chart"}, "skill": "WRITING", "category": "WRITING_T1_TYPE"},
        {"code": "WRITING_T1_TABLE", "name": {"vi": "Bảng số liệu", "en": "Table"}, "skill": "WRITING", "category": "WRITING_T1_TYPE"},
        {"code": "WRITING_T1_MIXED_CHARTS", "name": {"vi": "Biểu đồ hỗn hợp", "en": "Mixed Charts"}, "skill": "WRITING", "category": "WRITING_T1_TYPE"},
        {"code": "WRITING_T1_PROCESS_DIAGRAM", "name": {"vi": "Biểu đồ quy trình", "en": "Process Diagram"}, "skill": "WRITING", "category": "WRITING_T1_TYPE"},
        {"code": "WRITING_T1_MAP", "name": {"vi": "Bản đồ", "en": "Map"}, "skill": "WRITING", "category": "WRITING_T1_TYPE"},

        # Writing Task 2
        {"code": "WRITING_T2_AGREE_DISAGREE", "name": {"vi": "Đồng ý hay Không đồng ý", "en": "Agree & Disagree"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_DISCUSS_BOTH_VIEWS", "name": {"vi": "Thảo luận hai quan điểm", "en": "Discuss Both Views"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_ADVANTAGES_DISADVANTAGES", "name": {"vi": "Lợi ích và Tác hại", "en": "Advantages & Disadvantages"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_ADVANTAGES_OUTWEIGH_DISADVANTAGES", "name": {"vi": "Lợi ích vượt trội hơn tác hại", "en": "Advantages Outweigh Disadvantages"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_PROBLEMS_SOLUTIONS", "name": {"vi": "Vấn đề và Giải pháp", "en": "Problems & Solutions"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_CAUSES_SOLUTIONS", "name": {"vi": "Nguyên nhân và Giải pháp", "en": "Causes & Solutions"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_CAUSES_EFFECTS", "name": {"vi": "Nguyên nhân và Tác động", "en": "Causes & Effects"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_POSITIVE_NEGATIVE_DEVELOPMENT", "name": {"vi": "Xu hướng tích cực hay tiêu cực", "en": "Positive or Negative Development"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},
        {"code": "WRITING_T2_TWO_PART_QUESTIONS", "name": {"vi": "Câu hỏi gồm 2 phần", "en": "Two-part Questions"}, "skill": "WRITING", "category": "WRITING_T2_TYPE"},

        # Speaking
        {"code": "SPEAKING_P1_PERSONAL_INFO", "name": {"vi": "Thông tin cá nhân", "en": "Personal Information"}, "skill": "SPEAKING", "category": "SPEAKING_P1_TYPE"},
        {"code": "SPEAKING_P1_WORK_STUDY", "name": {"vi": "Công việc / Học tập", "en": "Work / Study"}, "skill": "SPEAKING", "category": "SPEAKING_P1_TYPE"},
        {"code": "SPEAKING_P1_HOMETOWN", "name": {"vi": "Quê hương", "en": "Hometown"}, "skill": "SPEAKING", "category": "SPEAKING_P1_TYPE"},
        {"code": "SPEAKING_P1_HOME_ACCOMMODATION", "name": {"vi": "Nhà cửa / Nơi ở", "en": "Home / Accommodation"}, "skill": "SPEAKING", "category": "SPEAKING_P1_TYPE"},
        {"code": "SPEAKING_P1_LIKES_DISLIKES", "name": {"vi": "Sở thích và Không thích", "en": "Likes & Dislikes"}, "skill": "SPEAKING", "category": "SPEAKING_P1_TYPE"},
        {"code": "SPEAKING_P1_HABITS_FREQUENCY", "name": {"vi": "Thói quen và Tần suất", "en": "Habits & Frequency"}, "skill": "SPEAKING", "category": "SPEAKING_P1_TYPE"},
        {"code": "SPEAKING_P1_PREFERENCES", "name": {"vi": "Sự ưu tiên", "en": "Preferences"}, "skill": "SPEAKING", "category": "SPEAKING_P1_TYPE"},
        {"code": "SPEAKING_P2_PERSON", "name": {"vi": "Mô tả một người", "en": "Describe a Person"}, "skill": "SPEAKING", "category": "SPEAKING_P2_TYPE"},
        {"code": "SPEAKING_P2_PLACE", "name": {"vi": "Mô tả một vật/địa điểm", "en": "Describe a Place"}, "skill": "SPEAKING", "category": "SPEAKING_P2_TYPE"},
        {"code": "SPEAKING_P2_EVENT", "name": {"vi": "Mô tả một sự kiện", "en": "Describe an Event"}, "skill": "SPEAKING", "category": "SPEAKING_P2_TYPE"},
        {"code": "SPEAKING_P3_DISCUSSION", "name": {"vi": "Thảo luận mở rộng", "en": "Discussion Topic"}, "skill": "SPEAKING", "category": "SPEAKING_P3_TYPE"},
    ]

    for tag_info in tags_data:
        res = await db.execute(select(Tag).filter(Tag.code == tag_info["code"]))
        existing = res.scalars().first()
        # Serialize name back to JSON string in db
        name_str = json.dumps(tag_info["name"])
        if not existing:
            new_tag = Tag(
                code=tag_info["code"],
                name=name_str,
                skill=tag_info["skill"],
                category=tag_info["category"]
            )
            db.add(new_tag)
        else:
            existing.name = name_str
            existing.skill = tag_info["skill"]
            existing.category = tag_info["category"]
    await db.commit()

    # 3. Seed Exams and their Questions
    # Query all tags to link them
    tags_res = await db.execute(select(Tag))
    all_tags = {tag.code: tag for tag in tags_res.scalars().all()}

    exams_data = [
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e01"),
            "title": {"vi": "Bar chart — Năng lượng tái tạo", "en": "Bar chart — Renewable energy consumption"},
            "description": "Biểu đồ cột so sánh tỷ trọng tiêu thụ năng lượng tái tạo của năm quốc gia qua các năm 2000, 2010, 2020.",
            "skill": "WRITING",
            "task_type": "TASK_1",
            "topic_id": TOPIC_IDS["environment"],
            "difficulty": "EASY",
            "duration_minutes": 20,
            "tag_codes": ["WRITING_T1_BAR_CHART"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f01"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_1",
                    "question_type": "WRITING_T1_BAR_CHART",
                    "title": "Renewable energy consumption",
                    "instructions": "Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
                    "content": {
                        "question": "The chart below shows renewable energy consumption as a percentage of total energy consumption in five countries (UK, USA, Germany, France, Japan) in 2000, 2010, and 2020.",
                        "image_url": "/seed/ielts/writing/task1/renewable-energy.png",
                        "minimum_words": 150
                    },
                    "metadata": {
                        "chart_type": "bar",
                        "year_range": ["2000", "2020"],
                        "countries": ["UK", "USA", "Germany", "France", "Japan"],
                        "units": "percentage"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e02"),
            "title": {"vi": "Bar chart — Sinh viên quốc tế", "en": "Bar chart — International students"},
            "description": "Biểu đồ cột so sánh số lượng sinh viên quốc tế nhập học ở một số quốc gia.",
            "skill": "WRITING",
            "task_type": "TASK_1",
            "topic_id": TOPIC_IDS["education"],
            "difficulty": "EASY",
            "duration_minutes": 20,
            "tag_codes": ["WRITING_T1_BAR_CHART"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f02"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_1",
                    "question_type": "WRITING_T1_BAR_CHART",
                    "title": "International students",
                    "instructions": "Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
                    "content": {
                        "question": "The chart below shows the percentage of international students in universities in various English-speaking countries in 2015 and 2020.",
                        "image_url": "/seed/ielts/writing/task1/international-students.png",
                        "minimum_words": 150
                    },
                    "metadata": {
                        "chart_type": "bar",
                        "year_range": ["2015", "2020"],
                        "units": "percentage"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e03"),
            "title": {"vi": "Bar chart — Chi tiêu y tế bình quân đầu người", "en": "Bar chart — Health spending per capita"},
            "description": "Biểu đồ cột so sánh chi tiêu y tế bình quân đầu người của một số quốc gia phát triển.",
            "skill": "WRITING",
            "task_type": "TASK_1",
            "topic_id": TOPIC_IDS["health"],
            "difficulty": "HARD",
            "duration_minutes": 20,
            "tag_codes": ["WRITING_T1_BAR_CHART"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f03"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_1",
                    "question_type": "WRITING_T1_BAR_CHART",
                    "title": "Health spending per capita",
                    "instructions": "Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
                    "content": {
                        "question": "The chart below shows the government health spending per capita in USD in six countries in 2019.",
                        "image_url": "/seed/ielts/writing/task1/health-spending.png",
                        "minimum_words": 150
                    },
                    "metadata": {
                        "chart_type": "bar",
                        "year": 2019,
                        "units": "USD"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e04"),
            "title": {"vi": "Làm việc từ xa — Lợi ích & Tác hại", "en": "Remote work — pros and cons"},
            "description": "Bài luận bàn về những lợi ích và tác hại của xu hướng làm việc từ xa.",
            "skill": "WRITING",
            "task_type": "TASK_2",
            "topic_id": TOPIC_IDS["technology"],
            "difficulty": "MEDIUM",
            "duration_minutes": 40,
            "tag_codes": ["WRITING_T2_ADVANTAGES_DISADVANTAGES"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f04"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_2",
                    "question_type": "WRITING_T2_ADVANTAGES_DISADVANTAGES",
                    "title": "Remote work pros and cons",
                    "instructions": "Give reasons for your answer and include any relevant examples from your own knowledge or experience.",
                    "content": {
                        "question": "These days, more and more people work remotely from home. Discuss the advantages and disadvantages of this development.",
                        "minimum_words": 250
                    },
                    "metadata": {
                        "essay_type": "advantages_disadvantages",
                        "requires_examples": True
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e05"),
            "title": {"vi": "Đồng phục học sinh — Ủng hộ hay Phản đối?", "en": "School uniforms — for or against?"},
            "description": "Bài luận nêu ý kiến cá nhân và thảo luận về tác động của việc mặc đồng phục học sinh.",
            "skill": "WRITING",
            "task_type": "TASK_2",
            "topic_id": TOPIC_IDS["education"],
            "difficulty": "EASY",
            "duration_minutes": 40,
            "tag_codes": ["WRITING_T2_AGREE_DISAGREE"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f05"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_2",
                    "question_type": "WRITING_T2_AGREE_DISAGREE",
                    "title": "School uniforms agree or disagree",
                    "instructions": "To what extent do you agree or disagree with this statement?",
                    "content": {
                        "question": "Some people believe that school uniforms should be compulsory for all students in school. To what extent do you agree or disagree?",
                        "minimum_words": 250
                    },
                    "metadata": {
                        "essay_type": "opinion"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e06"),
            "title": {"vi": "Cấm nhựa dùng một lần", "en": "Banning single-use plastics"},
            "description": "Bài luận bàn về việc cấm hoàn toàn nhựa dùng một lần để bảo vệ môi trường.",
            "skill": "WRITING",
            "task_type": "TASK_2",
            "topic_id": TOPIC_IDS["environment"],
            "difficulty": "MEDIUM",
            "duration_minutes": 40,
            "tag_codes": ["WRITING_T2_AGREE_DISAGREE"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f06"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_2",
                    "question_type": "WRITING_T2_AGREE_DISAGREE",
                    "title": "Banning single-use plastics",
                    "instructions": "To what extent do you agree or disagree?",
                    "content": {
                        "question": "Government should ban single-use plastics globally to solve the worsening environment. To what extent do you agree or disagree?",
                        "minimum_words": 250
                    },
                    "metadata": {
                        "essay_type": "opinion"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e07"),
            "title": {"vi": "Già hóa dân số", "en": "Ageing population"},
            "description": "Bài luận phân tích những ảnh hưởng tích cực/tiêu cực của vấn đề già hóa dân số đối với xã hội.",
            "skill": "WRITING",
            "task_type": "TASK_2",
            "topic_id": TOPIC_IDS["society"],
            "difficulty": "HARD",
            "duration_minutes": 40,
            "tag_codes": ["WRITING_T2_PROBLEMS_SOLUTIONS"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f07"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_2",
                    "question_type": "WRITING_T2_PROBLEMS_SOLUTIONS",
                    "title": "Ageing population",
                    "instructions": "What are the problems associated with this, and what measures can be taken to solve them?",
                    "content": {
                        "question": "In many countries, the proportion of older people is increasing. What are the problems associated with this, and what measures can be taken to solve them?",
                        "minimum_words": 250
                    },
                    "metadata": {
                        "essay_type": "problems_solutions"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e08"),
            "title": {"vi": "Đề thi trọn gói — Đô thị hóa & Giao thông", "en": "Full Test — Urbanisation & transport"},
            "description": "Đề thi trọn gói IELTS Writing gồm Task 1 (Line Graph) và Task 2 (Discussion) về chủ đề Phát triển đô thị.",
            "skill": "WRITING",
            "task_type": "FULL_TEST",
            "topic_id": TOPIC_IDS["society"],
            "difficulty": "MEDIUM",
            "duration_minutes": 60,
            "tag_codes": ["WRITING_T1_LINE_GRAPH", "WRITING_T2_DISCUSS_BOTH_VIEWS"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f08"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_1",
                    "question_type": "WRITING_T1_LINE_GRAPH",
                    "title": "Urban transit usage",
                    "instructions": "Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
                    "content": {
                        "question": "The line graph below shows population transport methods in a major city over 30 years from 1990 to 2020.",
                        "image_url": "/seed/ielts/writing/task1/urban-transit.png",
                        "minimum_words": 150
                    },
                    "metadata": {
                        "chart_type": "line",
                        "year_range": ["1990", "2020"]
                    }
                },
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f82"),
                    "order_index": 2,
                    "skill": "WRITING",
                    "task_type": "TASK_2",
                    "question_type": "WRITING_T2_DISCUSS_BOTH_VIEWS",
                    "title": "Car usage restriction",
                    "instructions": "Discuss both these views and give your opinion.",
                    "content": {
                        "question": "Some people believe that the best way to reduce traffic congestion in cities is to restrict car usage. Others argue that rebuilding roads is a better option. Discuss both these views and give your opinion.",
                        "minimum_words": 250
                    },
                    "metadata": {
                        "essay_type": "discuss_both_views"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e09"),
            "title": {"vi": "Đề thi trọn gói — Công nghệ trong giáo dục", "en": "Full Test — Technology in education"},
            "description": "Đề thi trọn gói IELTS Writing gồm Task 1 (Process Diagram) và Task 2 (Two-part questions).",
            "skill": "WRITING",
            "task_type": "FULL_TEST",
            "topic_id": TOPIC_IDS["technology"],
            "difficulty": "HARD",
            "duration_minutes": 60,
            "tag_codes": ["WRITING_T1_PROCESS_DIAGRAM", "WRITING_T2_TWO_PART_QUESTIONS"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f09"),
                    "order_index": 1,
                    "skill": "WRITING",
                    "task_type": "TASK_1",
                    "question_type": "WRITING_T1_PROCESS_DIAGRAM",
                    "title": "Recycling process of digital devices",
                    "instructions": "Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
                    "content": {
                        "question": "The diagram below shows how old computer systems and digital devices are recycled for school reuse.",
                        "image_url": "/seed/ielts/writing/task1/computer-recycling.png",
                        "minimum_words": 150
                    },
                    "metadata": {
                        "chart_type": "process"
                    }
                },
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f92"),
                    "order_index": 2,
                    "skill": "WRITING",
                    "task_type": "TASK_2",
                    "question_type": "WRITING_T2_TWO_PART_QUESTIONS",
                    "title": "Computers replacing school teachers",
                    "instructions": "Give reasons for your answer and include any relevant examples from your own knowledge or experience.",
                    "content": {
                        "question": "Computers are increasingly used in education. What are the benefits of this, and will they ever replace classrooms teachers?",
                        "minimum_words": 250
                    },
                    "metadata": {
                        "essay_type": "two_part_questions"
                    }
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e10"),
            "title": {"vi": "Luyện nói Speaking — Công việc & Học hỏi", "en": "Speaking Practice — Work & Study"},
            "description": "Luyện tập Speaking Part 1 về chủ đề Học tập và Công việc hiện tại của bạn.",
            "skill": "SPEAKING",
            "task_type": "TASK_1",
            "topic_id": TOPIC_IDS["education"],
            "difficulty": "EASY",
            "duration_minutes": 5,
            "tag_codes": ["SPEAKING_P1_WORK_STUDY"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f10"),
                    "order_index": 1,
                    "skill": "SPEAKING",
                    "task_type": "TASK_1",
                    "question_type": "SPEAKING_P1_WORK_STUDY",
                    "title": "Work and Study talk",
                    "instructions": "Answer the general speaking questions clearly.",
                    "content": {
                        "question": "Do you work or study? What do you like most about your curriculum/job? Why?",
                        "minimum_words": 0
                    },
                    "metadata": {}
                }
            ]
        },
        {
            "id": uuid.UUID("01a01a00-0000-7000-a000-000000000e11"),
            "title": {"vi": "Speaking Cue Card — Người truyền cảm hứng", "en": "Speaking Cue Card — Describe an inspiring person"},
            "description": "Luyện tập IELTS Speaking Part 2 mô tả một người truyền cảm hứng sâu sắc cho bạn.",
            "skill": "SPEAKING",
            "task_type": "TASK_2",
            "topic_id": TOPIC_IDS["society"],
            "difficulty": "MEDIUM",
            "duration_minutes": 10,
            "tag_codes": ["SPEAKING_P2_PERSON"],
            "questions": [
                {
                    "id": uuid.UUID("01a01a00-0000-7000-a000-000000000f11"),
                    "order_index": 1,
                    "skill": "SPEAKING",
                    "task_type": "TASK_2",
                    "question_type": "SPEAKING_P2_PERSON",
                    "title": "Describe an inspiring person",
                    "instructions": "Describe a person who has had a positive influence on you. You should say who they are, how you know them, and why they inspired you.",
                    "content": {
                        "question": "Describe an inspiring person. You should talk about who they are, how you know them, what they did, and explain why they inspire you.",
                        "minimum_words": 0
                    },
                    "metadata": {}
                }
            ]
        }
    ]

    for exam_info_raw in exams_data:
        exam_info = cast(Dict[str, Any], exam_info_raw)
        # Check if Exam exists
        res = await db.execute(select(Exam).options(selectinload(Exam.tags)).filter(Exam.id == exam_info["id"]))
        existing_exam = res.scalars().first()

        # Prepare tags list
        exam_tags_list = []
        tag_codes = cast(List[str], exam_info["tag_codes"])
        for code in tag_codes:
            if code in all_tags:
                exam_tags_list.append(all_tags[code])

        title_json = json.dumps(exam_info["title"])
        if not existing_exam:
            new_exam = Exam(
                id=exam_info["id"],
                title=title_json,
                description=exam_info["description"],
                skill=exam_info["skill"],
                task_type=exam_info["task_type"],
                topic_id=exam_info["topic_id"],
                difficulty=exam_info["difficulty"],
                duration_minutes=exam_info["duration_minutes"],
                status="PUBLISHED",
                tags=exam_tags_list
            )
            db.add(new_exam)
            existing_exam = new_exam
        else:
            existing_exam.title = title_json
            existing_exam.description = exam_info["description"]
            existing_exam.skill = exam_info["skill"]
            existing_exam.task_type = exam_info["task_type"]
            existing_exam.topic_id = exam_info["topic_id"]
            existing_exam.difficulty = exam_info["difficulty"]
            existing_exam.duration_minutes = exam_info["duration_minutes"]
            existing_exam.tags = exam_tags_list
        await db.commit()

        # Update or Insert Questions
        questions = cast(List[Dict[str, Any]], exam_info["questions"])
        for q_info in questions:
            res_q = await db.execute(select(ExamQuestion).filter(ExamQuestion.id == q_info["id"]))
            existing_q = res_q.scalars().first()
            if not existing_q:
                new_q = ExamQuestion(
                    id=q_info["id"],
                    exam_id=existing_exam.id,
                    order_index=q_info["order_index"],
                    skill=q_info["skill"],
                    task_type=q_info["task_type"],
                    question_type=q_info["question_type"],
                    title=q_info["title"],
                    instructions=q_info["instructions"],
                    content=q_info["content"],
                    question_metadata=q_info["metadata"]
                )
                db.add(new_q)
            else:
                existing_q.order_index = q_info["order_index"]
                existing_q.skill = q_info["skill"]
                existing_q.task_type = q_info["task_type"]
                existing_q.question_type = q_info["question_type"]
                existing_q.title = q_info["title"]
                existing_q.instructions = q_info["instructions"]
                existing_q.content = q_info["content"]
                existing_q.question_metadata = q_info["metadata"]
            await db.commit()

    # 4. Seed a default testing user if not exists
    user_res = await db.execute(select(User).filter(User.email == "test@example.com"))
    existing_user = user_res.scalars().first()
    if not existing_user:
        hashed_password = get_password_hash("password123")
        test_user = User(
            id=uuid.UUID("01a01a00-0000-7000-a000-000000000999"),
            email="test@example.com",
            name="Testing Acc",
            password_hash=hashed_password,
            email_verified=True,
            role="USER"
        )
        db.add(test_user)
        await db.commit()

    print("[SUCCESS] Seeded IELTS Library successfully!")

# Run script when called from CLI
if __name__ == "__main__":
    async def main():
        print("Starting seed script...")
        # Create async session manually
        engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)
        async_session = AsyncSession(engine)
        async with async_session as session:
            await seed_ielts_library(session)
        print("Done!")
    asyncio.run(main())
