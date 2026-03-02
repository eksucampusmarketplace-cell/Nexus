"""Authentication router."""

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import APIKey, Group, Member, User
from shared.schemas import AuthTokenRequest, AuthTokenResponse, UserPermissionsResponse

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = os.getenv("ENCRYPTION_KEY", "your-secret-key-min-32-characters-long")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """Verify Telegram WebApp initData."""
    try:
        if not init_data or not bot_token:
            raise ValueError("Missing init_data or bot_token")

        # Parse init data - keep raw values for hash, decode for reading
        raw_params = {}
        for param in init_data.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                raw_params[key] = value

        received_hash = raw_params.get("hash")
        if not received_hash:
            raise ValueError("Missing hash in init data")

        # Validate auth_date to prevent replay attacks (24 hour window)
        auth_date = raw_params.get("auth_date")
        if auth_date:
            import time
            auth_timestamp = int(auth_date)
            current_time = int(time.time())
            if current_time - auth_timestamp > 86400:  # 24 hours
                raise ValueError("Init data expired")

        # Create data_check_string using RAW (URL-encoded) values
        # Sort alphabetically by key, exclude hash
        data_check_items = []
        for key in sorted(raw_params.keys()):
            if key != "hash":
                data_check_items.append(f"{key}={raw_params[key]}")
        data_check_string = "\n".join(data_check_items)

        # Compute secret key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256,
        ).digest()

        # Compute hash
        computed_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        if computed_hash != received_hash:
            raise ValueError("Hash mismatch")

        # Parse user data with proper URL decoding
        from urllib.parse import unquote
        user_json = unquote(raw_params.get("user", "{}"))
        user_data = json.loads(user_json)
        return user_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid init data: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_api_key_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, APIKey]:
    """Get user from API key."""
    token = credentials.credentials
    if not token.startswith("nx_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    # Hash the key
    key_hash = hashlib.sha256(token.encode()).hexdigest()

    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        )
    )
    api_key = result.scalar()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key expired")

    # Update last used
    api_key.last_used = datetime.utcnow()
    await db.commit()

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user, api_key


@router.post("/auth/token", response_model=AuthTokenResponse)
async def create_token(
    request: AuthTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create access token from Telegram initData."""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="Bot token not configured")

    # Verify init data
    telegram_user = verify_telegram_init_data(request.init_data, bot_token)

    # Get or create user
    telegram_id = telegram_user.get("id")
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=telegram_user.get("username"),
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name"),
            language_code=telegram_user.get("language_code"),
            is_premium=telegram_user.get("is_premium", False),
        )
        db.add(user)
        await db.flush()

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    return AuthTokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    )


@router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": current_user.id,
        "telegram_id": current_user.telegram_id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "language_code": current_user.language_code,
        "is_premium": current_user.is_premium,
    }


@router.get("/auth/permissions/{group_id}", response_model=UserPermissionsResponse)
async def get_permissions(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user permissions in a group."""
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    is_owner = member.role == "owner"
    is_admin = member.role in ("owner", "admin")
    is_moderator = member.role in ("owner", "admin", "mod")

    return UserPermissionsResponse(
        is_owner=is_owner,
        is_admin=is_admin,
        is_moderator=is_moderator,
        can_manage_modules=is_admin,
        can_moderate=is_moderator,
        permissions=[
            "read:members",
            "write:moderation" if is_moderator else None,
            "write:modules" if is_admin else None,
            "write:settings" if is_owner else None,
        ],
    )
