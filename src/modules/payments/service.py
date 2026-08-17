import base64
import hashlib
import hmac
import random
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.config import settings
from src.models.auth import User
from src.models.payments import Order
from src.modules.payments import paypal_client
from src.modules.payments.constants import (
    ORDER_STATUS_PAID,
    ORDER_STATUS_PENDING,
    ORDER_CODE_ALPHABET,
    ORDER_CODE_SUFFIX_LEN,
    PAYMENT_PROVIDER_PAYPAL,
    PAYMENT_PROVIDER_SEPAY,
    PG_FIELD_ORDER,
    PG_NOTIFICATION_ORDER_PAID,
    PG_OPERATION_PURCHASE,
    PG_PAYMENT_METHOD_BANK_TRANSFER,
    PLAN_PREMIUM_1M,
    PLAN_PREMIUM_DAYS,
    PLAN_PRICE_PAYPAL_USD_CENTS,
    PLAN_PRICE_VND,
)
from src.modules.payments.schemas import SePayPGWebhookPayload


def _generate_order_code() -> str:
    suffix = "".join(random.choices(ORDER_CODE_ALPHABET, k=ORDER_CODE_SUFFIX_LEN))
    return f"{settings.SEPAY_PAYMENT_CODE_PREFIX}{suffix}"


def _resolve_plan_pricing(plan: Optional[str], provider: str) -> tuple[str, int, str, int]:
    plan = plan or PLAN_PREMIUM_1M
    prices = PLAN_PRICE_VND if provider == PAYMENT_PROVIDER_SEPAY else PLAN_PRICE_PAYPAL_USD_CENTS
    if plan not in prices:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")

    amount = prices[plan]
    currency = "VND" if provider == PAYMENT_PROVIDER_SEPAY else "USD"
    premium_days = PLAN_PREMIUM_DAYS[plan]
    return plan, amount, currency, premium_days


async def _create_pending_order(
    db: AsyncSession,
    user: User,
    plan: Optional[str],
    provider: str = PAYMENT_PROVIDER_SEPAY,
    order_code: Optional[str] = None,
) -> Order:
    plan, amount, currency, premium_days = _resolve_plan_pricing(plan, provider)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ORDER_EXPIRE_MINUTES)

    if order_code is not None:
        order = Order(
            user_id=user.id,
            order_code=order_code,
            plan=plan,
            amount=amount,
            currency=currency,
            status=ORDER_STATUS_PENDING,
            premium_days=premium_days,
            payment_provider=provider,
            expires_at=expires_at,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    for _ in range(5):
        order = Order(
            user_id=user.id,
            order_code=_generate_order_code(),
            plan=plan,
            amount=amount,
            currency=currency,
            status=ORDER_STATUS_PENDING,
            premium_days=premium_days,
            payment_provider=provider,
            expires_at=expires_at,
        )
        db.add(order)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        await db.refresh(order)
        return order

    raise HTTPException(status_code=500, detail="Could not generate a unique order code")


def _build_pg_signature(fields: dict) -> str:
    signed_str = ",".join(f"{key}={fields[key]}" for key in PG_FIELD_ORDER)
    digest = hmac.new(
        settings.SEPAY_PG_SECRET_KEY.encode(),
        signed_str.encode(),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode()


async def create_pg_checkout(db: AsyncSession, user: User, plan: Optional[str], locale: Optional[str]) -> dict:
    user_id = str(user.id)
    order = await _create_pending_order(db, user, plan)
    locale = locale or "vi"

    return_base = f"{settings.FRONTEND_BASE_URL}/{locale}/premium?order_id={order.id}"
    fields = {
        "merchant": settings.SEPAY_PG_MERCHANT_ID,
        "env": settings.SEPAY_PG_ENV,
        "operation": PG_OPERATION_PURCHASE,
        "payment_method": PG_PAYMENT_METHOD_BANK_TRANSFER,
        "order_amount": str(order.amount),
        "currency": order.currency,
        "order_invoice_number": order.order_code,
        "order_description": f"{order.plan} premium subscription",
        "customer_id": user_id,
        "success_url": f"{return_base}&payment=success",
        "error_url": f"{return_base}&payment=error",
        "cancel_url": f"{return_base}&payment=cancel",
    }
    signature = _build_pg_signature(fields)

    return {"checkout_url": settings.SEPAY_PG_CHECKOUT_URL, "fields": {**fields, "signature": signature}}


def order_to_response_dict(order: Order) -> dict:
    return {
        "id": str(order.id),
        "order_code": order.order_code,
        "plan": order.plan,
        "amount": order.amount,
        "currency": order.currency,
        "status": order.status,
        "payment_provider": order.payment_provider,
        "expires_at": order.expires_at,
        "created_at": order.created_at,
    }


async def get_order_for_user(db: AsyncSession, user: User, order_id: UUID) -> Order:
    result = await db.execute(select(Order).filter(Order.id == order_id, Order.user_id == user.id))
    order = result.scalars().first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _as_aware_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def get_premium_status(user: User) -> dict:
    now = datetime.now(timezone.utc)
    premium_until = _as_aware_utc(user.premium_until)
    is_premium = bool(premium_until and premium_until > now)
    return {"is_premium": is_premium, "premium_until": user.premium_until}


async def verify_sepay_pg_ipn_secret(request: Request) -> bytes:
    # This merchant account's IPN has no dashboard-level auth-type/secret setting, so SePay's
    # real sandbox notifications carry no X-Secret-Key at all. We still enforce it if a merchant
    # ever configures one and sends it, but can't require it unconditionally without breaking
    # every real delivery. Before production: add server-to-server confirmation against SePay's
    # Orders REST API (Basic Auth) before crediting premium, rather than trusting this body alone.
    provided = request.headers.get("X-Secret-Key")
    if provided is not None:
        expected = settings.SEPAY_PG_IPN_SECRET or settings.SEPAY_PG_SECRET_KEY
        if not hmac.compare_digest(expected, provided):
            raise HTTPException(status_code=401, detail="Invalid X-Secret-Key header")

    return await request.body()


async def _credit_order_paid(db: AsyncSession, order: Order, user: User, transaction_id: str, raw_payload: dict) -> None:
    now = datetime.now(timezone.utc)
    current_premium_until = _as_aware_utc(user.premium_until)
    base = current_premium_until if (current_premium_until and current_premium_until > now) else now
    user.premium_until = base + timedelta(days=order.premium_days)

    order.status = ORDER_STATUS_PAID
    order.paid_at = now
    order.pg_transaction_id = transaction_id
    order.raw_webhook_payload = raw_payload

    await db.commit()


async def process_sepay_pg_ipn(db: AsyncSession, payload: SePayPGWebhookPayload) -> None:
    if payload.notification_type != PG_NOTIFICATION_ORDER_PAID:
        return

    result = await db.execute(
        select(Order).filter(Order.order_code == payload.order.order_invoice_number).with_for_update()
    )
    order = result.scalars().first()
    if order is None:
        return

    if order.pg_transaction_id == payload.transaction.id:
        return

    if order.status == ORDER_STATUS_PAID:
        return

    result = await db.execute(select(User).filter(User.id == order.user_id).with_for_update())
    user = result.scalars().first()
    if user is None:
        return

    await _credit_order_paid(db, order, user, payload.transaction.id, payload.model_dump())


async def create_paypal_order(db: AsyncSession, user: User, plan: Optional[str]) -> dict:
    _, amount_cents, currency, _ = _resolve_plan_pricing(plan, PAYMENT_PROVIDER_PAYPAL)
    amount_str = f"{amount_cents / 100:.2f}"

    try:
        paypal_order = await paypal_client.create_order(amount_str, currency)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="PayPal order creation failed") from e

    order = await _create_pending_order(
        db, user, plan, provider=PAYMENT_PROVIDER_PAYPAL, order_code=paypal_order["id"]
    )
    return {"order_id": str(order.id), "paypal_order_id": paypal_order["id"]}


async def capture_paypal_order(db: AsyncSession, user: User, order_id: UUID) -> Order:
    order = await get_order_for_user(db, user, order_id)
    if order.payment_provider != PAYMENT_PROVIDER_PAYPAL:
        raise HTTPException(status_code=400, detail="Order is not a PayPal order")

    result = await db.execute(select(Order).filter(Order.id == order_id).with_for_update())
    order = result.scalars().first()
    if order.status == ORDER_STATUS_PAID:
        return order

    try:
        capture_result = await paypal_client.capture_order(order.order_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="PayPal capture failed") from e

    if capture_result.get("status") != "COMPLETED":
        raise HTTPException(status_code=402, detail="Payment not completed")

    capture_id = capture_result["purchase_units"][0]["payments"]["captures"][0]["id"]

    result = await db.execute(select(User).filter(User.id == order.user_id).with_for_update())
    order_user = result.scalars().first()

    await _credit_order_paid(db, order, order_user, capture_id, capture_result)
    await db.refresh(order)
    return order
