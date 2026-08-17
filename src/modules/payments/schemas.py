from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CreateCheckoutRequest(BaseModel):
    plan: Optional[str] = None
    locale: Optional[str] = "vi"


class CheckoutResponse(BaseModel):
    checkout_url: str
    fields: dict


class OrderResponse(BaseModel):
    id: str
    order_code: str
    plan: str
    amount: int
    currency: str
    status: str
    payment_provider: str
    expires_at: datetime
    created_at: datetime


class CreatePaypalOrderRequest(BaseModel):
    plan: Optional[str] = None


class CreatePaypalOrderResponse(BaseModel):
    order_id: str
    paypal_order_id: str


class PremiumStatusResponse(BaseModel):
    is_premium: bool
    premium_until: Optional[datetime] = None


class SePayPGOrderPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    order_invoice_number: str
    # TODO: confirm remaining leaf fields once a real sandbox IPN payload is observed


class SePayPGTransactionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    # TODO: confirm remaining leaf fields (amount? status?) once a real sandbox IPN payload is observed


class SePayPGWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    notification_type: str
    order: SePayPGOrderPayload
    transaction: SePayPGTransactionPayload
