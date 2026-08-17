from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from src.modules.payments import paypal_client

CREATE_URL = "/api/v1/payments/paypal/create-order"


async def _register_and_get_token(async_client: AsyncClient, email: str) -> str:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "name": "Test User"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _completed_capture(capture_id: str) -> dict:
    return {
        "status": "COMPLETED",
        "purchase_units": [{"payments": {"captures": [{"id": capture_id}]}}],
    }


async def _create_paypal_order(async_client: AsyncClient, token: str, monkeypatch, paypal_order_id: str) -> dict:
    monkeypatch.setattr(paypal_client, "create_order", AsyncMock(return_value={"id": paypal_order_id}))
    response = await async_client.post(
        CREATE_URL, json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_paypal_order_requires_auth(async_client: AsyncClient):
    response = await async_client.post(CREATE_URL, json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_paypal_order_creates_pending_usd_order(async_client: AsyncClient, monkeypatch):
    token = await _register_and_get_token(async_client, "paypal-buyer@example.com")
    data = await _create_paypal_order(async_client, token, monkeypatch, "FAKE_PAYPAL_ID_1")
    assert data["paypal_order_id"] == "FAKE_PAYPAL_ID_1"

    order_response = await async_client.get(
        f"/api/v1/payments/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    order = order_response.json()["data"]
    assert order["amount"] == 399
    assert order["currency"] == "USD"
    assert order["payment_provider"] == "PAYPAL"
    assert order["order_code"] == "FAKE_PAYPAL_ID_1"


@pytest.mark.asyncio
async def test_capture_paypal_order_marks_paid_and_extends_premium(async_client: AsyncClient, monkeypatch):
    token = await _register_and_get_token(async_client, "paypal-payer@example.com")
    data = await _create_paypal_order(async_client, token, monkeypatch, "FAKE_PAYPAL_ID_2")

    monkeypatch.setattr(paypal_client, "capture_order", AsyncMock(return_value=_completed_capture("CAP123")))
    response = await async_client.post(
        f"/api/v1/payments/paypal/capture/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    order = response.json()["data"]
    assert order["status"] == "PAID"

    order_response = await async_client.get(
        f"/api/v1/payments/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_response.json()["data"]["status"] == "PAID"

    premium = await async_client.get(
        "/api/v1/payments/premium-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert premium.json()["data"]["is_premium"] is True


@pytest.mark.asyncio
async def test_capture_paypal_order_rejects_non_completed_status(async_client: AsyncClient, monkeypatch):
    token = await _register_and_get_token(async_client, "paypal-pending@example.com")
    data = await _create_paypal_order(async_client, token, monkeypatch, "FAKE_PAYPAL_ID_3")

    monkeypatch.setattr(
        paypal_client, "capture_order", AsyncMock(return_value={"status": "PENDER", "purchase_units": []})
    )
    response = await async_client.post(
        f"/api/v1/payments/paypal/capture/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 402

    order_response = await async_client.get(
        f"/api/v1/payments/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_response.json()["data"]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_capture_paypal_order_idempotent_on_double_call(async_client: AsyncClient, monkeypatch):
    token = await _register_and_get_token(async_client, "paypal-double@example.com")
    data = await _create_paypal_order(async_client, token, monkeypatch, "FAKE_PAYPAL_ID_4")

    monkeypatch.setattr(paypal_client, "capture_order", AsyncMock(return_value=_completed_capture("CAP456")))
    await async_client.post(
        f"/api/v1/payments/paypal/capture/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    premium_after_first = await async_client.get(
        "/api/v1/payments/premium-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    premium_until_first = premium_after_first.json()["data"]["premium_until"]

    response = await async_client.post(
        f"/api/v1/payments/paypal/capture/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    premium_after_second = await async_client.get(
        "/api/v1/payments/premium-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert premium_after_second.json()["data"]["premium_until"] == premium_until_first


@pytest.mark.asyncio
async def test_capture_paypal_order_scoped_to_owner(async_client: AsyncClient, monkeypatch):
    token_a = await _register_and_get_token(async_client, "paypal-owner-a@example.com")
    token_b = await _register_and_get_token(async_client, "paypal-owner-b@example.com")
    data = await _create_paypal_order(async_client, token_a, monkeypatch, "FAKE_PAYPAL_ID_5")

    response = await async_client.post(
        f"/api/v1/payments/paypal/capture/{data['order_id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_paypal_token_is_cached_between_calls(monkeypatch):
    monkeypatch.setattr(paypal_client, "_token_cache", {"access_token": None, "expires_at": 0.0})
    fetch_mock = AsyncMock(return_value=("tok", 32400))
    monkeypatch.setattr(paypal_client, "_fetch_new_token", fetch_mock)

    await paypal_client.get_access_token(client=object())
    await paypal_client.get_access_token(client=object())

    assert fetch_mock.call_count == 1
