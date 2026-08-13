import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password123", "name": "Test User"}
    )
    
    # Try again
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password123", "name": "Test User"}
    )
    assert response.status_code == 400
    assert response.json()["message"] == "Email already registered"

@pytest.mark.asyncio
async def test_login(async_client: AsyncClient):
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "password123", "name": "Test User"}
    )
    
    # Login
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "invalid@example.com", "password": "password123", "name": "Test User"}
    )
    
    # Login with wrong password
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "invalid@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
