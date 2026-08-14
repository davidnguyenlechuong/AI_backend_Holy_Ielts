from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google.oauth2 import id_token
from google.auth.transport import requests
from src.db.dependencies import get_db
from src.models.auth import User, RefreshToken, AuthAccount
from src.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, hash_token
from src.core.config import settings
from src.modules.auth.schemas import UserCreate, UserLogin, TokenResponse, RefreshTokenRequest, GoogleAuthRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, name=user_in.name, password_hash=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    db_refresh_token = RefreshToken(
    user_id=new_user.id,
    token_hash=hash_token(refresh_token),
    expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
)
    db.add(db_refresh_token)
    await db.commit()
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_in.email))
    user = result.scalars().first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    db_refresh_token = RefreshToken(
    user_id=user.id,
    token_hash=hash_token(refresh_token),
    expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
)
    db.add(db_refresh_token)
    await db.commit()
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/google", response_model=TokenResponse)
async def google_login(request_data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Verify the Google JWT token
        idinfo = id_token.verify_oauth2_token(
            request_data.token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        email = idinfo.get('email')
        name = idinfo.get('name')
        sub = idinfo.get('sub') # Google Account ID
        
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # Check if user exists
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        
        if not user:
            # Create user
            user = User(email=email, name=name, email_verified=True)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Create AuthAccount link
            auth_account = AuthAccount(user_id=user.id, provider="google", provider_account_id=sub)
            db.add(auth_account)
            await db.commit()
            
        # Generate our own tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        db_refresh_token = RefreshToken(
    user_id=user.id,
    token_hash=hash_token(refresh_token),
    expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
)
        db.add(db_refresh_token)
        await db.commit()
        
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
