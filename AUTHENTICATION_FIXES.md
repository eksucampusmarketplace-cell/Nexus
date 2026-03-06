# Authentication Fixes for Nexus Mini App

## Issues Identified

Based on the logs showing "Authentication Failed" and Redis connection errors, I identified several issues:

### 1. Redis Connection Failures (Non-Critical)
The logs showed:
```
2026-03-06 14:57:19,669 | ERROR | shared.event_bus | Failed to publish event: Error 111 connecting to localhost:6379. Connection refused.
```

This was causing errors in the event bus but not blocking authentication directly.

### 2. Mini App Authentication for Private Chat Users
When users open the Mini App from a private chat (not a group) and haven't added the bot to any groups yet, authentication fails because:
- The `initData` doesn't contain a `chat_id`
- The user has no group memberships to look up bot tokens from
- All bot token validation attempts fail with hash mismatch

### 3. Unclear Error Messages
The error messages were too technical and didn't guide users on how to fix the issue.

## Fixes Applied

### 1. Redis Graceful Degradation
**File: `shared/redis_client.py`**

Added a mock Redis client that allows the application to run without Redis:
- If Redis connection fails, a mock client is used instead
- The mock client logs what would happen but doesn't crash
- Features using Redis (Event Bus, Rate Limiting) will be disabled gracefully
- App continues to function for core features

```python
async def get_redis() -> aioredis.Redis:
    """Get or create global Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await _redis_pool.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Redis features will be disabled.")
            _redis_pool = _create_mock_redis()
    return _redis_pool
```

### 2. Improved Authentication Error Messages
**File: `api/routers/auth.py`**

Rewrote the error message logic to provide context-specific guidance:

- **For users not in any groups**: Clear steps to add bot to a group
- **For users with hash mismatches**: Explain what might be wrong and alternatives
- **For missing user info**: Explain they need to open from Telegram

```python
if chat_id is None and not request.bot_token:
    if telegram_user_id and not user_bot_tokens:
        error_detail = (
            "You're not a member of any groups with Nexus yet. "
            "To get started, either:\n\n"
            "1. Add the bot to a group and send a message\n"
            "2. Open the Mini App from that group (menu → Mini App)\n\n"
            "Or use a custom bot token if you have your own bot from @BotFather."
        )
```

### 3. Better Error Display in Mini App
**File: `mini-app/src/views/EntrySelection.tsx`**

- Added support for multi-line error messages with `whitespace-pre-line` class
- Added a debug button for development mode to check API diagnostic endpoint
- Updated "First Time Setup" instructions to be more specific

### 4. Public Diagnostic Endpoint
**File: `api/main.py`**

Added `/api/diagnostic` endpoint that returns:
- Whether BOT_TOKEN is configured
- Environment settings
- Helpful tips for common issues

```python
@app.get("/api/diagnostic")
async def diagnostic_info():
    """Public diagnostic endpoint for troubleshooting Mini App issues."""
    return {
        "status": "ok",
        "bot_token_configured": bot_token_set,
        "environment": environment,
        "mini_app_url": os.getenv("MINI_APP_URL"),
        "websocket_url": os.getenv("WEBHOOK_URL"),
        "tips": {
            "if_not_configured": "Make sure BOT_TOKEN is set in environment variables",
            "if_auth_fails": "Ensure you're opening Mini App from a group with bot installed",
            "if_no_groups": "Add the bot to a Telegram group and send a message first"
        }
    }
```

## How to Test the Fixes

1. **Redis Unavailable**:
   - The app will now start without Redis and log warnings instead of crashing
   - Event bus features will be disabled but core functionality works

2. **Authentication from Private Chat**:
   - Users opening Mini App from private chat will see clear guidance
   - Three paths are offered:
     a. Add bot to a group (with specific bot username)
     b. Use custom bot token
     c. Read first-time setup guide

3. **Better Error Messages**:
   - Error messages now have line breaks for readability
   - Each error provides actionable next steps

## User Flow After Fixes

### Scenario 1: User Opens from Private Chat (Not in Groups)
1. Mini App detects private chat context
2. Shows "Entry Selection" screen
3. User clicks "Use Existing Groups"
4. Authentication fails with clear message:
   > "You're not a member of any groups with Nexus yet.
   > To get started, either:
   > 
   > 1. Add the bot to a group and send a message
   > 2. Open the Mini App from that group (menu → Mini App)
   > 
   > Or use a custom bot token if you have your own bot from @BotFather."

### Scenario 2: User Opens from Group
1. Mini App receives `initData` with `chat_id`
2. Bot token is looked up from database for that group
3. Hash validation succeeds
4. User is authenticated and redirected to group dashboard

### Scenario 3: User Has Custom Bot Token
1. User clicks "Add Custom Bot Token"
2. Enters bot token from @BotFather
3. Hash validation succeeds with that token
4. User is authenticated and can manage that group

## Important Notes

1. **BOT_TOKEN Must Be Set**: Ensure the `BOT_TOKEN` environment variable is set in production
2. **Group Context is Best**: The Mini App works best when opened from a group with the bot installed
3. **Redis is Optional**: With these fixes, the app can run without Redis (with limited features)
4. **Custom Tokens Supported**: Users can bring their own bots via the custom token feature

## Files Modified

- `shared/redis_client.py` - Added graceful Redis fallback
- `api/routers/auth.py` - Improved error messages
- `api/main.py` - Added diagnostic endpoint
- `mini-app/src/views/EntrySelection.tsx` - Better error display and guidance
