"""Authentication router."""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import parse_qsl, unquote

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import APIKey, Group, Member, User, BotInstance
from shared.schemas import AuthTokenRequest, AuthTokenResponse, UserPermissionsResponse

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# In production, ENCRYPTION_KEY must be explicitly set
_env_encryption_key = os.getenv("ENCRYPTION_KEY")
_environment = os.getenv("ENVIRONMENT", "development")

if _env_encryption_key:
    SECRET_KEY = _env_encryption_key
elif _environment == "production":
    raise RuntimeError(
        "ENCRYPTION_KEY environment variable is required in production. "
        "Please set a secure encryption key (min 32 characters)."
    )
else:
    # Development fallback - DO NOT use in production
    SECRET_KEY = "your-secret-key-min-32-characters-long"

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


def parse_init_data(init_data: str) -> Tuple[dict, dict, str]:
    """
    Parse Telegram WebApp initData without validation.
    
    Returns:
        Tuple of (raw_params, parsed_data, received_hash)
    """
    raw_params = {}
    for param in init_data.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            raw_params[key] = value
    
    received_hash = raw_params.get("hash", "")
    
    # Parse user data with proper URL decoding
    parsed_data = {}
    
    user_json = unquote(raw_params.get("user", "{}"))
    if user_json:
        try:
            parsed_data["user"] = json.loads(user_json)
        except json.JSONDecodeError:
            pass
    
    # Parse chat info if present
    if raw_params.get("chat"):
        chat_json = unquote(raw_params.get("chat", "{}"))
        try:
            parsed_data["chat"] = json.loads(chat_json)
        except json.JSONDecodeError:
            pass
    
    if raw_params.get("chat_type"):
        parsed_data["chat_type"] = raw_params.get("chat_type")
    
    if raw_params.get("start_param"):
        parsed_data["start_param"] = raw_params.get("start_param")
    
    if raw_params.get("auth_date"):
        parsed_data["auth_date"] = raw_params.get("auth_date")
    
    return raw_params, parsed_data, received_hash


def validate_init_data_hash(raw_params: dict, bot_token: str) -> bool:
    """
    Validate the hash of Telegram WebApp initData.
    
    Returns True if valid, False otherwise.
    """
    received_hash = raw_params.get("hash", "")
    if not received_hash:
        return False
    
    # Validate auth_date to prevent replay attacks (24 hour window)
    auth_date = raw_params.get("auth_date")
    if auth_date:
        import time
        auth_timestamp = int(auth_date)
        current_time = int(time.time())
        if current_time - auth_timestamp > 86400:  # 24 hours
            logger.warning(f"Init data expired: auth_date={auth_timestamp}, current={current_time}")
            return False
    
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
        logger.debug(f"Hash mismatch: computed={computed_hash[:16]}..., received={received_hash[:16]}...")
        return False
    
    return True


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """Verify Telegram WebApp initData."""
    try:
        if not init_data or not bot_token:
            raise ValueError("Missing init_data or bot_token")

        raw_params, parsed_data, received_hash = parse_init_data(init_data)

        if not received_hash:
            raise ValueError("Missing hash in init data")

        if not validate_init_data_hash(raw_params, bot_token):
            raise ValueError("Hash mismatch")

        # Return combined user and chat data
        user_data = parsed_data.get("user", {})
        result = user_data.copy() if user_data else {}
        
        if parsed_data.get("chat"):
            result["chat"] = parsed_data["chat"]
        if parsed_data.get("chat_type"):
            result["chat_type"] = parsed_data["chat_type"]
        if parsed_data.get("start_param"):
            result["start_param"] = parsed_data["start_param"]

        return result

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
    """Create access token from Telegram initData.
    
    This endpoint validates Telegram WebApp init data and creates a JWT token.
    It supports both shared bot mode and white-label mode (custom bot tokens).
    
    The validation tries bot tokens in this order:
    1. Custom bot token provided in request (from localStorage)
    2. Bot token from BotInstance table (looked up by chat ID from init data)
    3. Main BOT_TOKEN environment variable
    """
    main_bot_token = os.getenv("BOT_TOKEN")
    
    # Parse init data first to extract chat info
    raw_params, parsed_data, received_hash = parse_init_data(request.init_data)
    
    if not received_hash:
        raise HTTPException(status_code=401, detail="Invalid init data: Missing hash")
    
    # Extract chat/telegram ID for bot token lookup
    chat_id = None
    if parsed_data.get("chat"):
        chat_id = parsed_data["chat"].get("id")
    if not chat_id and parsed_data.get("start_param"):
        # Try to parse start_param as group ID
        try:
            chat_id = int(parsed_data["start_param"])
        except (ValueError, TypeError):
            pass
    
    # Collect error messages for debugging
    validation_errors = []
    
    # Try 1: Custom bot token from request (localStorage)
    if request.bot_token:
        logger.info(f"Trying custom bot token from request (length: {len(request.bot_token)})")
        if validate_init_data_hash(raw_params, request.bot_token):
            logger.info("Validation successful with custom bot token from request")
            telegram_user = verify_telegram_init_data(request.init_data, request.bot_token)
            return await _create_user_token(telegram_user, db)
        else:
            validation_errors.append("Custom bot token: hash mismatch")
            logger.warning("Custom bot token validation failed")
    
    # Try 2: Look up bot token from BotInstance table by chat ID
    if chat_id:
        logger.info(f"Looking up bot token for chat_id: {chat_id}")
        bot_instance = await _get_bot_token_for_chat(db, chat_id)
        if bot_instance:
            logger.info(f"Found bot instance for chat {chat_id}: @{bot_instance.get('username', 'unknown')}")
            if validate_init_data_hash(raw_params, bot_instance['token']):
                logger.info(f"Validation successful with bot token for chat {chat_id}")
                telegram_user = verify_telegram_init_data(request.init_data, bot_instance['token'])
                return await _create_user_token(telegram_user, db)
            else:
                validation_errors.append(f"Bot token for chat {chat_id}: hash mismatch")
                logger.warning(f"Bot token for chat {chat_id} validation failed")
    
    # Try 3: Main bot token from environment
    if main_bot_token:
        logger.info("Trying main BOT_TOKEN from environment")
        if validate_init_data_hash(raw_params, main_bot_token):
            logger.info("Validation successful with main BOT_TOKEN")
            telegram_user = verify_telegram_init_data(request.init_data, main_bot_token)
            return await _create_user_token(telegram_user, db)
        else:
            validation_errors.append("Main BOT_TOKEN: hash mismatch")
            logger.warning("Main BOT_TOKEN validation failed")
    
    # All validation attempts failed
    error_detail = "Invalid init data: Hash mismatch"
    if validation_errors:
        error_detail += f" (tried: {', '.join(validation_errors)})"
    
    logger.error(f"All validation attempts failed. Chat ID: {chat_id}, Errors: {validation_errors}")
    raise HTTPException(status_code=401, detail=error_detail)


async def _get_bot_token_for_chat(db: AsyncSession, telegram_chat_id: int) -> Optional[dict]:
    """
    Get the bot token for a specific Telegram chat from the BotInstance table.
    
    Args:
        telegram_chat_id: The Telegram chat ID (from init data)
    
    Returns dict with 'token' and 'username' if found, None otherwise.
    """
    try:
        # First, find the group by Telegram ID
        group_result = await db.execute(
            select(Group).where(Group.telegram_id == telegram_chat_id)
        )
        group = group_result.scalar_one_or_none()
        
        if not group:
            logger.debug(f"No group found with telegram_id={telegram_chat_id}")
            return None
        
        # Then, find the bot instance for this group
        bot_result = await db.execute(
            select(BotInstance).where(
                BotInstance.group_id == group.id,
                BotInstance.is_active == True
            )
        )
        bot_instance = bot_result.scalar_one_or_none()
        
        if not bot_instance:
            logger.debug(f"No active bot instance found for group_id={group.id}")
            return None
        
        # Decrypt the stored token
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            logger.warning("ENCRYPTION_KEY not set, cannot decrypt bot token")
            return None
        
        fernet = Fernet(encryption_key.encode())
        decrypted_token = fernet.decrypt(bot_instance.token_hash.encode()).decode()
        
        return {
            'token': decrypted_token,
            'username': bot_instance.bot_username,
            'bot_id': bot_instance.bot_telegram_id,
        }
    except Exception as e:
        logger.error(f"Error getting bot token for chat {telegram_chat_id}: {e}")
        return None


async def _create_user_token(telegram_user: dict, db: AsyncSession) -> AuthTokenResponse:
    """Create or get user and return access token."""
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


@router.post("/auth/debug")
async def debug_auth(
    request: AuthTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Debug endpoint to diagnose authentication issues.
    
    This endpoint returns detailed information about the init data validation
    without actually creating a token. Useful for debugging hash mismatch issues.
    """
    import time
    
    main_bot_token = os.getenv("BOT_TOKEN")
    
    # Parse init data
    raw_params, parsed_data, received_hash = parse_init_data(request.init_data)
    
    # Extract chat info - prefer chat.id over start_param
    chat_id = None
    if parsed_data.get("chat"):
        chat_id = parsed_data["chat"].get("id")
    if not chat_id and parsed_data.get("start_param"):
        try:
            chat_id = int(parsed_data["start_param"])
        except (ValueError, TypeError):
            pass
    
    # Check auth_date
    auth_date_valid = True
    auth_date_age = None
    if parsed_data.get("auth_date"):
        auth_timestamp = int(parsed_data["auth_date"])
        current_time = int(time.time())
        auth_date_age = current_time - auth_timestamp
        auth_date_valid = auth_date_age <= 86400
    
    # Build debug info
    debug_info = {
        "init_data_length": len(request.init_data),
        "has_hash": bool(received_hash),
        "hash_length": len(received_hash) if received_hash else 0,
        "raw_params_keys": list(raw_params.keys()),
        "parsed_data_keys": list(parsed_data.keys()),
        "user_id": parsed_data.get("user", {}).get("id") if parsed_data.get("user") else None,
        "chat_id": chat_id,
        "auth_date": parsed_data.get("auth_date"),
        "auth_date_age_seconds": auth_date_age,
        "auth_date_valid": auth_date_valid,
        "start_param": parsed_data.get("start_param"),
        "has_custom_bot_token": bool(request.bot_token),
        "has_main_bot_token": bool(main_bot_token),
        "validation_results": {},
    }
    
    # Try validation with each token
    if request.bot_token:
        debug_info["validation_results"]["custom_token"] = {
            "valid": validate_init_data_hash(raw_params, request.bot_token),
            "token_length": len(request.bot_token),
        }
    
    if chat_id:
        bot_instance = await _get_bot_token_for_chat(db, chat_id)
        if bot_instance:
            debug_info["validation_results"]["db_token"] = {
                "valid": validate_init_data_hash(raw_params, bot_instance['token']),
                "bot_username": bot_instance.get('username'),
            }
        else:
            debug_info["validation_results"]["db_token"] = {"found": False}
    
    if main_bot_token:
        debug_info["validation_results"]["main_token"] = {
            "valid": validate_init_data_hash(raw_params, main_bot_token),
        }
    
    return debug_info
