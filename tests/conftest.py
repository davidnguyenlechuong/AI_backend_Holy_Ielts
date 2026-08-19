import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.main import app
from src.db.dependencies import get_db
from src.db.base import Base
import src.models

from sqlalchemy.pool import StaticPool
import sqlalchemy as sa

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import UUID as BaseUUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

@compiles(BaseUUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

@compiles(PG_UUID, "sqlite")
def compile_uuid_pg_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

# File-based SQLite for testing to prevent connection isolation issues
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_dev.db"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def db_setup_teardown():
    # Setup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        result = await conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
        print("ACTUAL TABLES IN DB AFTER CREATE_ALL:", result.scalars().all())
    yield
    # Teardown
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
