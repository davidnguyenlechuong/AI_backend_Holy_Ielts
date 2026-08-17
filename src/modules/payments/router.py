import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dependencies import get_db
from src.models.auth import User
from src.modules.auth.dependencies import get_current_user
from src.modules.payments import service
from src.modules.payments.schemas import CreateCheckoutRequest, CreatePaypalOrderRequest, SePayPGWebhookPayload
from src.shared.responses.base import ResponseSchema

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/checkout", response_model=ResponseSchema)
async def create_checkout(
    body: CreateCheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    checkout = await service.create_pg_checkout(db, user, body.plan, body.locale)
    return ResponseSchema(message="Checkout created", data=checkout)


@router.get("/orders/{order_id}", response_model=ResponseSchema)
async def get_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await service.get_order_for_user(db, user, order_id)
    return ResponseSchema(message="Order status", data=service.order_to_response_dict(order))


@router.get("/premium-status", response_model=ResponseSchema)
async def premium_status(user: User = Depends(get_current_user)):
    return ResponseSchema(message="Premium status", data=await service.get_premium_status(user))


@router.post("/paypal/create-order", response_model=ResponseSchema)
async def create_paypal_order(
    body: CreatePaypalOrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.create_paypal_order(db, user, body.plan)
    return ResponseSchema(message="PayPal order created", data=result)


@router.post("/paypal/capture/{order_id}", response_model=ResponseSchema)
async def capture_paypal_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await service.capture_paypal_order(db, user, order_id)
    return ResponseSchema(message="PayPal payment captured", data=service.order_to_response_dict(order))


@router.post("/webhook/sepay-pg")
async def sepay_pg_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await service.verify_sepay_pg_ipn_secret(request)
    payload = SePayPGWebhookPayload.model_validate_json(raw_body)
    try:
        await service.process_sepay_pg_ipn(db, payload)
    except HTTPException:
        raise
    except Exception:
        pass
    return {"success": True}
