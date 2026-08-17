import base64
import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient

from src.core.config import settings
from src.modules.payments.constants import PG_FIELD_ORDER

IPN_URL = "/api/v1/payments/webhook/sepay-pg"


def _ipn_headers() -> dict:
    secret = settings.SEPAY_PG_IPN_SECRET or settings.SEPAY_PG_SECRET_KEY
    return {"X-Secret-Key": secret}


def _ipn_payload(tx_id: str, order_invoice_number: str, notification_type: str = "ORDER_PAID") -> bytes:
    payload = {
        "notification_type": notification_type,
        "order": {"order_invoice_number": order_invoice_number},
        "transaction": {"id": tx_id},
    }
    return json.dumps(payload).encode()


def _expected_signature(fields: dict) -> str:
    signed_str = ",".join(f"{key}={fields[key]}" for key in PG_FIELD_ORDER)
    digest = hmac.new(
        settings.SEPAY_PG_SECRET_KEY.encode(),
        signed_str.encode(),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode()


async def _register_and_get_token(async_client: AsyncClient, email: str) -> str:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "name": "Test User"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _create_checkout(async_client: AsyncClient, token: str) -> dict:
    response = await async_client.post(
        "/api/v1/payments/checkout",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _create_checkout_and_get_order(async_client: AsyncClient, token: str) -> tuple[dict, dict]:
    checkout = await _create_checkout(async_client, token)
    order_id = checkout["fields"]["success_url"].split("order_id=")[1].split("&")[0]
    order_response = await async_client.get(
        f"/api/v1/payments/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_response.status_code == 200
    return checkout, order_response.json()["data"]


@pytest.mark.asyncio
async def test_create_checkout_requires_auth(async_client: AsyncClient):
    response = await async_client.post("/api/v1/payments/checkout", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_checkout_returns_signed_fields(async_client: AsyncClient):
    token = await _register_and_get_token(async_client, "buyer@example.com")
    checkout = await _create_checkout(async_client, token)

    fields = checkout["fields"]
    for key in PG_FIELD_ORDER:
        assert key in fields
    assert fields["order_invoice_number"].startswith(settings.SEPAY_PAYMENT_CODE_PREFIX)
    assert fields["merchant"] == settings.SEPAY_PG_MERCHANT_ID
    assert checkout["checkout_url"] == settings.SEPAY_PG_CHECKOUT_URL

    assert fields["signature"] == _expected_signature(fields)


@pytest.mark.asyncio
async def test_get_order_scoped_to_owner(async_client: AsyncClient):
    token_a = await _register_and_get_token(async_client, "owner-a@example.com")
    token_b = await _register_and_get_token(async_client, "owner-b@example.com")
    _, order = await _create_checkout_and_get_order(async_client, token_a)

    response = await async_client.get(
        f"/api/v1/payments/orders/{order['id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ipn_rejects_wrong_secret_when_sent(async_client: AsyncClient):
    body = _ipn_payload(tx_id="1", order_invoice_number="PREMIUMBADCODE1")
    response = await async_client.post(IPN_URL, content=body, headers={"X-Secret-Key": "wrong-secret"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ipn_accepts_missing_secret_header(async_client: AsyncClient):
    # Real SePay sandbox IPN deliveries carry no X-Secret-Key at all for this merchant account.
    body = _ipn_payload(tx_id="2", order_invoice_number="PREMIUMNOKEY001")
    response = await async_client.post(IPN_URL, content=body)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ipn_marks_order_paid_and_extends_premium(async_client: AsyncClient):
    token = await _register_and_get_token(async_client, "payer@example.com")
    _, order = await _create_checkout_and_get_order(async_client, token)

    body = _ipn_payload(tx_id="tx-100", order_invoice_number=order["order_code"])
    response = await async_client.post(IPN_URL, content=body, headers=_ipn_headers())
    assert response.status_code == 200
    assert response.json() == {"success": True}

    order_check = await async_client.get(
        f"/api/v1/payments/orders/{order['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_check.json()["data"]["status"] == "PAID"

    premium = await async_client.get(
        "/api/v1/payments/premium-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert premium.json()["data"]["is_premium"] is True


@pytest.mark.asyncio
async def test_ipn_idempotent_on_duplicate_delivery(async_client: AsyncClient):
    token = await _register_and_get_token(async_client, "dup-payer@example.com")
    _, order = await _create_checkout_and_get_order(async_client, token)

    body = _ipn_payload(tx_id="tx-200", order_invoice_number=order["order_code"])
    await async_client.post(IPN_URL, content=body, headers=_ipn_headers())

    premium_after_first = await async_client.get(
        "/api/v1/payments/premium-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    premium_until_first = premium_after_first.json()["data"]["premium_until"]

    # Re-deliver the exact same transaction id
    response = await async_client.post(IPN_URL, content=body, headers=_ipn_headers())
    assert response.status_code == 200

    premium_after_second = await async_client.get(
        "/api/v1/payments/premium-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert premium_after_second.json()["data"]["premium_until"] == premium_until_first


@pytest.mark.asyncio
async def test_ipn_ignores_unknown_order(async_client: AsyncClient):
    body = _ipn_payload(tx_id="tx-300", order_invoice_number="PREMIUMUNKNOWN01")
    response = await async_client.post(IPN_URL, content=body, headers=_ipn_headers())
    assert response.status_code == 200
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_ipn_ignores_non_order_paid_notification(async_client: AsyncClient):
    token = await _register_and_get_token(async_client, "other-notif@example.com")
    _, order = await _create_checkout_and_get_order(async_client, token)

    body = _ipn_payload(tx_id="tx-400", order_invoice_number=order["order_code"], notification_type="ORDER_PENDING")
    response = await async_client.post(IPN_URL, content=body, headers=_ipn_headers())
    assert response.status_code == 200

    order_check = await async_client.get(
        f"/api/v1/payments/orders/{order['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_check.json()["data"]["status"] == "PENDING"

