"""Authentication router."""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
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

# JWT Secret Configuration
# In production, JWT_SECRET must be explicitly set for security
_jwt_secret = os.getenv("JWT_SECRET")
_env_encryption_key = os.getenv("ENCRYPTION_KEY")
_environment = os.getenv("ENVIRONMENT", "development")

if _jwt_secret:
    # Prefer dedicated JWT_SECRET if available
    SECRET_KEY = _jwt_secret
elif _env_encryption_key:
    # Fall back to ENCRYPTION_KEY for backward compatibility
    SECRET_KEY = _env_encryption_key
elif _environment == "production":
    raise RuntimeError(
        "JWT_SECRET environment variable is required in production. "
        "Please set a secure JWT secret (min 32 characters). "
        "You can also use ENCRYPTION_KEY for backward compatibility."
    )
else:
    # Development fallback - DO NOT use in production
    SECRET_KEY = "dev-jwt-secret-do-not-use-in-production"

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
    Parse Telegram WebApp initData.

    CRITICAL: We must preserve the ORIGINAL URL-encoded values for hash validation.
    Telegram computes the hash using the raw initData string values, NOT URL-decoded ones.

    Example: If user="John%20Doe" in initData, Telegram uses "John%20Doe" for hash,
    but parse_qsl would decode it to "John Doe", causing hash mismatch.

    Returns:
        Tuple of (raw_params_encoded, parsed_data, received_hash)
    """
    import urllib.parse

    # Split manually to preserve URL-encoded values for hash computation
    # This is critical - Telegram uses the original URL-encoded values for hash
    # Note: We can't use parse_qsl because it URL-decodes values by default
    raw_params_encoded = {}
    for pair in init_data.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            raw_params_encoded[key] = value
        elif pair:
            raw_params_encoded[pair] = ""

    received_hash = raw_params_encoded.get("hash", "")

    parsed_data = {}

    # For user and chat, we need to URL-decode the JSON before parsing
    user_raw = raw_params_encoded.get("user", "")
    if user_raw:
        try:
            decoded_user = urllib.parse.unquote(user_raw)
            parsed_data["user"] = json.loads(decoded_user)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                f"Failed to parse user JSON: {e}, raw value: {user_raw[:100]!r}"
            )

    chat_raw = raw_params_encoded.get("chat", "")
    if chat_raw:
        try:
            decoded_chat = urllib.parse.unquote(chat_raw)
            parsed_data["chat"] = json.loads(decoded_chat)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                f"Failed to parse chat JSON: {e}, raw value: {chat_raw[:100]!r}"
            )

    if raw_params_encoded.get("chat_type"):
        parsed_data["chat_type"] = raw_params_encoded.get("chat_type")

    if raw_params_encoded.get("start_param"):
        parsed_data["start_param"] = raw_params_encoded.get("start_param")

    if raw_params_encoded.get("auth_date"):
        parsed_data["auth_date"] = raw_params_encoded.get("auth_date")

    return raw_params_encoded, parsed_data, received_hash


def validate_init_data_hash(raw_params: dict, bot_token: str) -> bool:
    """
    Validate the hash of Telegram WebApp initData.

    Uses the official Telegram algorithm:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

    Returns True if valid, False otherwise.
    """
    import urllib.parse

    logger.debug("[HASH] Starting hash validation...")
    
    received_hash = raw_params.get("hash", "")
    if not received_hash:
        logger.warning("[HASH] Missing hash in init data")
        return False

    logger.debug(f"[HASH] Received hash (first 30 chars): {received_hash[:30]}...")
    logger.debug(f"[HASH] Bot token (first 10 chars): {bot_token[:10]!r}...")

    # Validate auth_date to prevent replay attacks (24 hour window)
    auth_date = raw_params.get("auth_date")
    if auth_date:
        import time

        auth_timestamp = int(auth_date)
        current_time = int(time.time())
        time_diff = current_time - auth_timestamp
        logger.debug(f"[HASH] Auth date check: timestamp={auth_timestamp}, current={current_time}, diff={time_diff}s")
        
        if time_diff > 86400:  # 24 hours
            logger.warning(
                f"[HASH] Init data expired: auth_date={auth_timestamp}, current={current_time}, diff={time_diff}s"
            )
            return False

    # Create a copy of params for hash computation
    # IMPORTANT: We must use the raw URL-encoded values as-is from the init data
    # Telegram uses the exact same string for hash computation
    parsed = dict(raw_params)

    # Extract and remove the hash — it must NOT be part of the check string
    parsed.pop("hash", None)

    # Also remove 'signature' if present — it's not part of the legacy hash check
    parsed.pop("signature", None)

    logger.debug(f"[HASH] Params for hash computation: {list(parsed.keys())}")

    # Build the data_check_string: sorted keys alphabetically, joined by \n
    # Use the raw URL-encoded values as per Telegram's algorithm
    # This is critical - Telegram uses the URL-encoded values directly
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    logger.debug(f"[HASH] Data check string (first 200 chars): {data_check_string[:200]!r}...")

    # Step 1: Derive secret key using "WebAppData" as the HMAC key
    # CRITICAL: key=b"WebAppData", msg=bot_token — NOT the other way around
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    logger.debug(f"[HASH] Secret key derived (hex): {secret_key.hex()[:32]}...")

    # Step 2: Compute the final hash using the derived secret key
    # Use the raw data_check_string bytes directly
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    logger.debug(f"[HASH] Computed hash (URL-encoded data): {computed_hash}")

    # Also try with the URL-decoded values as a fallback
    # Some implementations may use URL-decoded values
    data_check_string_decoded = "\n".join(
        f"{k}={urllib.parse.unquote(v)}" for k, v in sorted(parsed.items())
    )
    computed_hash_decoded = hmac.new(
        key=secret_key,
        msg=data_check_string_decoded.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    logger.debug(f"[HASH] Computed hash (URL-decoded data): {computed_hash_decoded}")

    # Use constant-time comparison to prevent timing attacks
    if hmac.compare_digest(computed_hash, received_hash):
        logger.debug("[HASH] Hash validated using URL-encoded data")
        return True

    # Try decoded version as fallback
    if hmac.compare_digest(computed_hash_decoded, received_hash):
        logger.info("[HASH] Hash validated using URL-decoded values (fallback)")
        return True

    # Log detailed debug info for diagnosis
    logger.warning(
        f"[HASH] MISMATCH: computed={computed_hash}, received={received_hash}"
    )
    logger.debug(f"[HASH] Data check string (URL-encoded, first 300): {data_check_string[:300]!r}")
    logger.debug(f"[HASH] Data check string (URL-decoded, first 300): {data_check_string_decoded[:300]!r}")
    return False


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


# Owner and Support ID configuration
OWNER_IDS = {
    int(id_str.strip())
    for id_str in os.getenv("OWNER_IDS", "").split(",")
    if id_str.strip()
}
SUPPORT_IDS = {
    int(id_str.strip())
    for id_str in os.getenv("SUPPORT_IDS", "").split(",")
    if id_str.strip()
}


def is_owner(telegram_id: int) -> bool:
    """Check if user is a bot owner."""
    return telegram_id in OWNER_IDS


def is_support(telegram_id: int) -> bool:
    """Check if user is support staff."""
    return telegram_id in SUPPORT_IDS


def is_staff(telegram_id: int) -> bool:
    """Check if user is owner or support staff."""
    return telegram_id in OWNER_IDS or telegram_id in SUPPORT_IDS


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


async def get_current_user_with_permissions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token with owner/support permissions attached."""
    user = await get_current_user(credentials, db)

    # Attach permission flags to user object
    user.is_owner = is_owner(user.telegram_id)
    user.is_support = is_support(user.telegram_id)
    user.is_staff = is_staff(user.telegram_id)

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
    # IMPORTANT: Strip whitespace from bot token to handle potential environment variable formatting issues
    main_bot_token = os.getenv("BOT_TOKEN", "").strip()

    # ========== EXTENSIVE DEBUG LOGGING ==========
    logger.info("=" * 60)
    logger.info("AUTH TOKEN REQUEST - EXTENSIVE DEBUG")
    logger.info("=" * 60)
    
    # Log the incoming request for debugging
    init_data_len = len(request.init_data) if request.init_data else 0
    logger.info(f"[AUTH] init_data length: {init_data_len}")
    logger.info(f"[AUTH] init_data (first 300 chars): {request.init_data[:300]!r}..." if request.init_data else "[AUTH] init_data: EMPTY")
    logger.info(f"[AUTH] Custom bot token provided: {bool(request.bot_token)}")
    logger.info(f"[AUTH] Main bot token configured: {bool(main_bot_token)}")
    
    if main_bot_token:
        logger.info(f"[AUTH] Main BOT_TOKEN: {main_bot_token[:10]}...{main_bot_token[-5:]}, length: {len(main_bot_token)}")
    else:
        logger.error("[AUTH] BOT_TOKEN environment variable is EMPTY or not set!")

    # Parse init data first to extract chat info
    raw_params, parsed_data, received_hash = parse_init_data(request.init_data)

    if not received_hash:
        logger.error("[AUTH] Missing hash in init data!")
        raise HTTPException(status_code=401, detail="Invalid init data: Missing hash")

    # Log parsed data for debugging
    logger.info(f"[AUTH] Raw params keys: {list(raw_params.keys())}")
    logger.info(f"[AUTH] Parsed data keys: {list(parsed_data.keys())}")
    
    # User info
    user_data = parsed_data.get('user', {})
    if user_data:
        logger.info(f"[AUTH] User from init_data:")
        logger.info(f"  - ID: {user_data.get('id')}")
        logger.info(f"  - Username: {user_data.get('username')}")
        logger.info(f"  - First name: {user_data.get('first_name')}")
        logger.info(f"  - Last name: {user_data.get('last_name')}")
        logger.info(f"  - Language: {user_data.get('language_code')}")
        logger.info(f"  - Is premium: {user_data.get('is_premium')}")
    else:
        logger.warning("[AUTH] No user data in init_data!")
    
    # Chat info
    chat_data = parsed_data.get('chat', {})
    if chat_data:
        logger.info(f"[AUTH] Chat from init_data:")
        logger.info(f"  - ID: {chat_data.get('id')}")
        logger.info(f"  - Type: {chat_data.get('type')}")
        logger.info(f"  - Title: {chat_data.get('title')}")
        logger.info(f"  - Username: {chat_data.get('username')}")
    else:
        logger.info("[AUTH] No chat data in init_data (may be private chat)")
    
    logger.info(f"[AUTH] Start param: {parsed_data.get('start_param')}")
    logger.info(f"[AUTH] Auth date: {parsed_data.get('auth_date')}")
    logger.info(f"[AUTH] Hash (first 20 chars): {received_hash[:20]}...")

    # Extract chat/telegram ID for bot token lookup
    chat_id = None
    if parsed_data.get("chat"):
        chat_id = parsed_data["chat"].get("id")
    if not chat_id and parsed_data.get("start_param"):
        # Try to parse start_param as group ID
        try:
            chat_id = int(parsed_data["start_param"])
            logger.info(f"[AUTH] Parsed chat_id from start_param: {chat_id}")
        except (ValueError, TypeError):
            logger.warning(f"[AUTH] Failed to parse start_param as int: {parsed_data.get('start_param')}")
            pass

    # Collect error messages for debugging
    validation_errors = []
    user_bot_tokens = []  # Track tokens from user's group memberships

    # Try 1: Get user from initData, then find bots based on user's group memberships
    # This is the database-driven approach - no localStorage needed
    telegram_user_data = parsed_data.get("user", {})
    telegram_user_id = telegram_user_data.get("id")
    
    logger.info(f"[AUTH] Starting token validation attempts for user_id: {telegram_user_id}")

    if telegram_user_id:
        # Get all bot tokens for groups where this user is a member
        logger.info(f"[AUTH] Attempt 1: Looking up bot tokens for user {telegram_user_id}...")
        user_bot_tokens = await _get_bot_tokens_for_user(db, telegram_user_id)
        logger.info(f"[AUTH] Found {len(user_bot_tokens)} bot tokens from user's group memberships")
        
        for bot_info in user_bot_tokens:
            bot_username = bot_info.get('username', 'unknown')
            group_id = bot_info.get('group_id')
            logger.info(f"[AUTH] Trying bot @{bot_username} from user membership (group_id: {group_id})")
            
            is_valid = validate_init_data_hash(raw_params, bot_info["token"])
            logger.info(f"[AUTH] Bot @{bot_username} hash validation: {'SUCCESS' if is_valid else 'FAILED'}")
            
            if is_valid:
                logger.info(f"[AUTH] Validation successful with user's bot @{bot_username}")
                telegram_user = verify_telegram_init_data(request.init_data, bot_info["token"])
                return await _create_user_token(telegram_user, db)
            else:
                validation_errors.append(f"User's bot @{bot_username}: hash mismatch")
                logger.debug(f"Bot @{bot_username} validation failed")

    # Note: If user is not in any groups yet (new user or private chat open),
    # user_bot_tokens will be empty. In this case, we fall through to try the
    # main bot token or all registered bot instances below.

    # Try 2: Custom bot token from request (fallback - deprecated, prefer database)
    # Strip whitespace from custom bot token as well
    custom_bot_token = request.bot_token.strip() if request.bot_token else None
    if custom_bot_token:
        logger.info(f"[AUTH] Attempt 2: Trying custom bot token from request (length: {len(custom_bot_token)})")
        is_valid = validate_init_data_hash(raw_params, custom_bot_token)
        logger.info(f"[AUTH] Custom bot token hash validation: {'SUCCESS' if is_valid else 'FAILED'}")
        
        if is_valid:
            logger.info("[AUTH] Validation successful with custom bot token from request")
            telegram_user = verify_telegram_init_data(request.init_data, custom_bot_token)
            return await _create_user_token(telegram_user, db)
        else:
            validation_errors.append("Custom bot token: hash mismatch")
            logger.warning("[AUTH] Custom bot token validation failed")

    # Try 3: Look up bot token from BotInstance table by chat ID
    if chat_id:
        logger.info(f"[AUTH] Attempt 3: Looking up bot token for chat_id: {chat_id}")
        bot_instance = await _get_bot_token_for_chat(db, chat_id)
        if bot_instance:
            bot_username = bot_instance.get('username', 'unknown')
            logger.info(f"[AUTH] Found bot instance for chat {chat_id}: @{bot_username}")
            
            is_valid = validate_init_data_hash(raw_params, bot_instance["token"])
            logger.info(f"[AUTH] Chat bot token hash validation: {'SUCCESS' if is_valid else 'FAILED'}")
            
            if is_valid:
                logger.info(f"[AUTH] Validation successful with bot token for chat {chat_id}")
                telegram_user = verify_telegram_init_data(request.init_data, bot_instance["token"])
                return await _create_user_token(telegram_user, db)
            else:
                validation_errors.append(f"Bot token for chat {chat_id}: hash mismatch")
                logger.warning(f"[AUTH] Bot token for chat {chat_id} validation failed")
        else:
            logger.info(f"[AUTH] No bot instance found for chat_id: {chat_id}")

    # Try 4: Try ALL bot instances from database (for private chat opens where no chat_id available)
    # This allows white-label/clone bots to authenticate from private chats
    logger.info("[AUTH] Attempt 4: Trying ALL bot instances from database...")
    all_bot_tokens = await _get_all_bot_tokens(db)
    logger.info(f"[AUTH] Found {len(all_bot_tokens)} total bot instances to try")
    
    for bot_info in all_bot_tokens:
        bot_username = bot_info.get('username', 'unknown')
        group_id = bot_info.get('group_id')
        logger.info(f"[AUTH] Trying bot instance @{bot_username} (group_id: {group_id})")
        
        is_valid = validate_init_data_hash(raw_params, bot_info["token"])
        logger.info(f"[AUTH] Bot @{bot_username} hash validation: {'SUCCESS' if is_valid else 'FAILED'}")
        
        if is_valid:
            logger.info(f"[AUTH] Validation successful with bot @{bot_username} (group_id: {group_id})")
            telegram_user = verify_telegram_init_data(request.init_data, bot_info["token"])
            return await _create_user_token(telegram_user, db)
        else:
            validation_errors.append(f"Bot @{bot_username}: hash mismatch")
            logger.debug(f"Bot @{bot_username} validation failed")

    # Try 5: Main bot token from environment
    if main_bot_token:
        logger.info("[AUTH] Attempt 5: Trying main BOT_TOKEN from environment")
        is_valid = validate_init_data_hash(raw_params, main_bot_token)
        logger.info(f"[AUTH] Main BOT_TOKEN hash validation: {'SUCCESS' if is_valid else 'FAILED'}")
        
        if is_valid:
            logger.info("[AUTH] Validation successful with main BOT_TOKEN")
            telegram_user = verify_telegram_init_data(request.init_data, main_bot_token)
            return await _create_user_token(telegram_user, db)
        else:
            validation_errors.append("Main BOT_TOKEN: hash mismatch")
            logger.warning("[AUTH] Main BOT_TOKEN validation failed")

    # All validation attempts failed
    logger.error("[AUTH] ALL VALIDATION ATTEMPTS FAILED")
    logger.error(f"[AUTH] Validation errors: {validation_errors}")
    
    error_detail = "Invalid init data: Hash mismatch"
    if validation_errors:
        error_detail += f" (tried: {', '.join(validation_errors)})"

    # Provide more helpful error message for common issues
    if chat_id is None and not request.bot_token:
        if telegram_user_id and not user_bot_tokens:
            # User opened from private chat but isn't in any groups with the bot
            error_detail += (
                ". You are not currently a member of any groups with this bot. "
                "Please add the bot to a group first, then open the Mini App from there. "
                "The Mini App works best when opened directly from a group."
            )
        else:
            error_detail += (
                ". Chat ID not found in initData and no custom bot token provided. "
            )
            error_detail += "Ensure BOT_TOKEN environment variable matches the bot that opened the Mini App."

    # Development bypass: Allow authentication without hash validation in development
    # This is useful for testing the Mini App in a browser without Telegram
    dev_bypass = os.getenv("DISABLE_AUTH_VALIDATION", "").lower() in (
        "true",
        "1",
        "yes",
    )
    if dev_bypass and _environment == "development":
        logger.warning(
            f"[AUTH] DEVELOPMENT MODE: Bypassing hash validation for user {parsed_data.get('user', {}).get('id')}"
        )
        if parsed_data.get("user"):
            return await _create_user_token(parsed_data["user"], db)

    logger.error(
        f"[AUTH] Final error - Chat ID: {chat_id}, Raw params keys: {list(raw_params.keys())}, Errors: {validation_errors}"
    )
    logger.info("=" * 60)
    raise HTTPException(status_code=401, detail=error_detail)


async def _get_bot_token_for_chat(
    db: AsyncSession, telegram_chat_id: int
) -> Optional[dict]:
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
                BotInstance.group_id == group.id, BotInstance.is_active == True
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
        decrypted_token = fernet.decrypt(bot_instance.token_hash.encode()).decode().strip()

        return {
            "token": decrypted_token,
            "username": bot_instance.bot_username,
            "bot_id": bot_instance.bot_telegram_id,
        }
    except Exception as e:
        logger.error(f"Error getting bot token for chat {telegram_chat_id}: {e}")
        return None


async def _get_all_bot_tokens(db: AsyncSession) -> list[dict]:
    """
    Get all active bot tokens from the BotInstance table.

    This is used when the Mini App is opened from a private chat (no chat_id),
    so we can try all registered bots to find the one that signed the initData.

    Returns list of dicts with 'token', 'username', 'bot_id', and 'group_id'.
    """
    try:
        # Get all active bot instances
        bot_result = await db.execute(
            select(BotInstance).where(BotInstance.is_active == True)
        )
        bot_instances = bot_result.scalars().all()

        if not bot_instances:
            logger.debug("No active bot instances found")
            return []

        # Decrypt each token
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            logger.warning("ENCRYPTION_KEY not set, cannot decrypt bot tokens")
            return []

        fernet = Fernet(encryption_key.encode())

        bots = []
        for bot_instance in bot_instances:
            try:
                decrypted_token = fernet.decrypt(
                    bot_instance.token_hash.encode()
                ).decode().strip()
                bots.append(
                    {
                        "token": decrypted_token,
                        "username": bot_instance.bot_username,
                        "bot_id": bot_instance.bot_telegram_id,
                        "group_id": bot_instance.group_id,
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to decrypt bot token for {bot_instance.bot_username}: {e}"
                )
                continue

        logger.info(f"Found {len(bots)} active bot instances to try")
        return bots

    except Exception as e:
        logger.error(f"Error getting all bot tokens: {e}")
        return []


async def _get_bot_tokens_for_user(
    db: AsyncSession, telegram_user_id: int
) -> list[dict]:
    """
    Get bot tokens for groups where the user is a member.

    This is the database-driven approach - the bot knows which groups
    the user belongs to and can find the right bot tokens automatically.
    No localStorage needed!

    Args:
        db: Database session
        telegram_user_id: The Telegram user ID from initData

    Returns list of dicts with 'token', 'username', 'bot_id', and 'group_id'.
    """
    try:
        # First, find the user by telegram_id
        user_result = await db.execute(
            select(User).where(User.telegram_id == telegram_user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            logger.debug(f"No user found with telegram_id={telegram_user_id}")
            return []

        # Get all groups where user is a member
        member_result = await db.execute(
            select(Member).where(Member.user_id == user.id)
        )
        members = member_result.scalars().all()

        if not members:
            logger.debug(f"User {telegram_user_id} is not a member of any groups")
            return []

        group_ids = [m.group_id for m in members]
        logger.info(
            f"User {telegram_user_id} is member of {len(group_ids)} groups: {group_ids}"
        )

        # Get all BotInstances for those groups
        bot_result = await db.execute(
            select(BotInstance).where(
                BotInstance.group_id.in_(group_ids), BotInstance.is_active == True
            )
        )
        bot_instances = bot_result.scalars().all()

        if not bot_instances:
            logger.debug(f"No active bot instances found for user's groups")
            return []

        # Decrypt each token
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            logger.warning("ENCRYPTION_KEY not set, cannot decrypt bot tokens")
            return []

        fernet = Fernet(encryption_key.encode())

        bots = []
        for bot_instance in bot_instances:
            try:
                decrypted_token = fernet.decrypt(
                    bot_instance.token_hash.encode()
                ).decode().strip()
                bots.append(
                    {
                        "token": decrypted_token,
                        "username": bot_instance.bot_username,
                        "bot_id": bot_instance.bot_telegram_id,
                        "group_id": bot_instance.group_id,
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to decrypt bot token for {bot_instance.bot_username}: {e}"
                )
                continue

        logger.info(f"Found {len(bots)} bot instances for user {telegram_user_id}")
        return bots

    except Exception as e:
        logger.error(f"Error getting bot tokens for user {telegram_user_id}: {e}")
        return []


async def _create_user_token(
    telegram_user: dict, db: AsyncSession
) -> AuthTokenResponse:
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
        user={
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "is_bot": user.is_bot,
            "is_premium": user.is_premium,
            "created_at": user.created_at,
            "updated_at": user.last_seen,
        },
    )


@router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info including owner/support permissions."""
    return {
        "id": current_user.id,
        "telegram_id": current_user.telegram_id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "language_code": current_user.language_code,
        "is_premium": current_user.is_premium,
        "is_owner": is_owner(current_user.telegram_id),
        "is_support": is_support(current_user.telegram_id),
        "is_staff": is_staff(current_user.telegram_id),
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

    # Strip whitespace from bot token
    main_bot_token = os.getenv("BOT_TOKEN", "").strip()

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
        "user_id": (
            parsed_data.get("user", {}).get("id") if parsed_data.get("user") else None
        ),
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
            "valid": validate_init_data_hash(raw_params, request.bot_token.strip()),
            "token_length": len(request.bot_token),
        }

    if chat_id:
        bot_instance = await _get_bot_token_for_chat(db, chat_id)
        if bot_instance:
            debug_info["validation_results"]["db_token"] = {
                "valid": validate_init_data_hash(raw_params, bot_instance["token"]),
                "bot_username": bot_instance.get("username"),
            }
        else:
            debug_info["validation_results"]["db_token"] = {"found": False}

    # Try all bot instances from database (for private chat scenarios)
    all_bots = await _get_all_bot_tokens(db)
    if all_bots:
        debug_info["validation_results"]["all_bot_instances"] = {
            "count": len(all_bots),
            "results": [],
        }
        for bot in all_bots:
            is_valid = validate_init_data_hash(raw_params, bot["token"])
            debug_info["validation_results"]["all_bot_instances"]["results"].append(
                {
                    "username": bot.get("username"),
                    "group_id": bot.get("group_id"),
                    "valid": is_valid,
                }
            )
            if is_valid:
                debug_info["validation_results"]["all_bot_instances"]["matched"] = (
                    bot.get("username")
                )

    if main_bot_token:
        debug_info["validation_results"]["main_token"] = {
            "valid": validate_init_data_hash(raw_params, main_bot_token),
        }

    return debug_info
