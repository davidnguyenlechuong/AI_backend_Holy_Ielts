import time

import httpx

from src.core.config import settings

_API_BASES = {
    "sandbox": "https://api-m.sandbox.paypal.com",
    "live": "https://api-m.paypal.com",
}

_token_cache: dict = {"access_token": None, "expires_at": 0.0}


def _api_base() -> str:
    return _API_BASES.get(settings.PAYPAL_ENV, _API_BASES["sandbox"])


async def _fetch_new_token(client: httpx.AsyncClient) -> tuple[str, float]:
    resp = await client.post(
        f"{_api_base()}/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID or "", settings.PAYPAL_CLIENT_SECRET or ""),
        data={"grant_type": "client_credentials"},
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"], data["expires_in"]


async def get_access_token(client: httpx.AsyncClient) -> str:
    if _token_cache["access_token"] and _token_cache["expires_at"] > time.monotonic() + 60:
        return _token_cache["access_token"]

    token, expires_in = await _fetch_new_token(client)
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = time.monotonic() + expires_in
    return token


async def create_order(amount: str, currency: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        token = await get_access_token(client)
        resp = await client.post(
            f"{_api_base()}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "intent": "CAPTURE",
                "purchase_units": [{"amount": {"currency_code": currency, "value": amount}}],
            },
        )
        resp.raise_for_status()
        return resp.json()


async def capture_order(paypal_order_id: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        token = await get_access_token(client)
        resp = await client.post(
            f"{_api_base()}/v2/checkout/orders/{paypal_order_id}/capture",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        resp.raise_for_status()
        return resp.json()
