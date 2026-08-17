import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "IELTS AI Platform"
    VERSION: str = "1.0.0"
    
    # DB Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ielts_ai"
    
    # Auth
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # AI Providers
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # SePay Payment Gateway (hosted checkout)
    SEPAY_API_KEY: Optional[str] = None
    SEPAY_PG_MERCHANT_ID: str = ""
    SEPAY_PG_SECRET_KEY: str = "changeme_sepay_pg_secret_key"
    SEPAY_PG_ENV: str = "sandbox"  # "sandbox" or "production" — sent as the `env` checkout field
    SEPAY_PG_IPN_SECRET: Optional[str] = None  # X-Secret-Key IPN auth value; falls back to SEPAY_PG_SECRET_KEY
    SEPAY_PG_CHECKOUT_URL: str = "https://pay-sandbox.sepay.vn/v1/checkout/init"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    SEPAY_PAYMENT_CODE_PREFIX: str = "PREMIUM"
    ORDER_EXPIRE_MINUTES: int = 15

    # PayPal (card + PayPal-account checkout)
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_ENV: str = "sandbox"  # "sandbox" or "live"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
