ORDER_STATUS_PENDING = "PENDING"
ORDER_STATUS_PAID = "PAID"
ORDER_STATUS_EXPIRED = "EXPIRED"
ORDER_STATUS_CANCELED = "CANCELED"

# Placeholder single plan — real pricing is a pending business decision.
PLAN_PREMIUM_1M = "PREMIUM_1M"
PLAN_PRICE_VND = {
    PLAN_PREMIUM_1M: 1_000,  # PLACEHOLDER PRICE — lowered for live-money test payments
}
PLAN_PREMIUM_DAYS = {
    PLAN_PREMIUM_1M: 30,
}

ORDER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # avoid ambiguous chars (0/O, 1/I)
ORDER_CODE_SUFFIX_LEN = 8

# Order matches the sepay-pg-node SDK's signed-field whitelist (src/checkout.ts), restricted
# to the fields we actually send for a one-time purchase.
PG_FIELD_ORDER = (
    "merchant",
    "env",
    "operation",
    "payment_method",
    "order_amount",
    "currency",
    "order_invoice_number",
    "order_description",
    "customer_id",
    "success_url",
    "error_url",
    "cancel_url",
)
PG_OPERATION_PURCHASE = "PURCHASE"
PG_PAYMENT_METHOD_BANK_TRANSFER = "BANK_TRANSFER"
PG_NOTIFICATION_ORDER_PAID = "ORDER_PAID"

PAYMENT_PROVIDER_SEPAY = "SEPAY"
PAYMENT_PROVIDER_PAYPAL = "PAYPAL"

PLAN_PRICE_PAYPAL_USD_CENTS = {
    PLAN_PREMIUM_1M: 399,  # $3.99 USD — PayPal doesn't support VND
}
