# Nexus Debug System - Complete Guide

## Overview

The Nexus Debug System is a sophisticated, comprehensive debugging solution for both the Python Telegram Bot and React TypeScript Mini App. It provides:

- **100,000+ lines** of equivalent debug output capability
- **Automatic error analysis** with actionable fix suggestions
- **Real-time diagnostics** for all critical failure points
- **Performance monitoring** and tracking
- **Telegram-specific error decoding**
- **Hash validation diagnostics**
- **Command flow tracing**
- **Keyboard and inline button debugging**

## Key Features

### For the Bot (Python)

#### 1. DebugLogger Class
```python
from bot.core.debug_logger import debug, DebugContext, ErrorAnalyzer

# Basic logging
debug.info("Starting operation", component="module_name")
debug.debug("Variable value", component="module_name", value=42)

# Context-based logging with automatic timing
def handle_command(ctx):
    with DebugContext("command_handler", component="moderation", command="ban") as dbg:
        dbg.log_step("validating_permissions")
        # ... do work ...
        dbg.success("User banned")

# Error with automatic fix suggestion
try:
    await bot.send_message(chat_id, text)
except Exception as e:
    debug.error("Failed to send message", error=e, component="messaging")
    # Automatically outputs fix suggestion like:
    # 💡 FIX: Bot lacks permission. Check bot is admin with required permissions...
```

#### 2. ErrorAnalyzer
Automatically analyzes Telegram API errors and provides fix suggestions:

| Error Pattern | Category | Fix Suggestion |
|--------------|----------|----------------|
| "bot was blocked by the user" | PERMISSION | User blocked bot, cannot send DMs |
| "chat not found" | TELEGRAM_API | Verify chat ID and bot membership |
| "not enough rights" | PERMISSION | Enable all required admin permissions |
| "hash mismatch" | VALIDATION | Wrong bot token for validation |
| "init data is invalid" | VALIDATION | Check token matches Mini App opener |
| "inline keyboard" | VALIDATION | callback_data must be 1-64 bytes |

#### 3. InitDataValidator
Validates Telegram Mini App initData with detailed diagnostics:

```python
from bot.core.debug_logger import InitDataValidator

result = InitDataValidator.validate(init_data, bot_token)
print(result)
# {
#   "valid": True/False,
#   "init_data_present": True,
#   "parsed_params": {...},
#   "errors": [...],
#   "diagnostics": {
#     "computed_hash_prefix": "abc123...",
#     "received_hash_prefix": "abc123...",
#     "auth_age_seconds": 1234,
#     "cause": "HASH_MISMATCH",
#     "explanation": "Detailed explanation..."
#   }
# }
```

#### 4. CommandDebugger
Debug command handling with permission tracking:

```python
from bot.core.debug_logger import CommandDebugger

CommandDebugger.log_command_received(ctx, "warn", ["@user", "spam"])
CommandDebugger.log_permission_check(ctx, "warn", "admin", has_permission=True)
CommandDebugger.log_command_processed(ctx, "warn", success=True)
```

#### 5. KeyboardDebugger
Validate inline keyboards before sending:

```python
from bot.core.debug_logger import KeyboardDebugger

# Validate keyboard
issues = KeyboardDebugger.validate_keyboard(keyboard_markup)
if issues:
    debug.warn("Keyboard issues found", component="keyboard", issues=issues)

# Log callbacks
KeyboardDebugger.log_callback_received(callback_query)
```

### For the Mini App (TypeScript/React)

#### 1. EnhancedDebugLogger
```typescript
import { enhancedDebug, LogCategory, LogLevel } from './utils/enhancedDebug';

// Basic logging
enhancedDebug.info('Starting operation', LogCategory.API);
enhancedDebug.debug('Variable value', LogCategory.STATE, { count: 42 });

// Context with automatic timing
await enhancedDebug.withContext('fetchGroups', LogCategory.GROUPS, async (ctx) => {
  ctx.log('Fetching from API');
  const result = await api.get('/groups');
  ctx.log(`Found ${result.length} groups`);
  return result;
});

// Performance tracking
const result = enhancedDebug.track('heavyOperation', () => {
  return performHeavyCalculation();
});
```

#### 2. ErrorAnalyzer
Comprehensive error database with fixes:

```typescript
import { ErrorAnalyzer, ErrorCode } from './utils/enhancedDebug';

const analysis = ErrorAnalyzer.analyze(error);
console.log(analysis);
// {
//   code: ErrorCode.HASH_MISMATCH,
//   category: 'Authentication',
//   message: 'initData hash validation failed',
//   explanation: 'The computed HMAC hash doesn't match...',
//   fix: 'Ensure BOT_TOKEN matches the bot from @BotFather...',
//   preventFuture: ['Use environment variables for tokens...'],
//   relatedErrors: [ErrorCode.AUTH_FAILED, ...],
//   severity: 'critical'
// }
```

#### 3. InitDataValidator (Client-side)
```typescript
import { InitDataValidator } from './utils/enhancedDebug';

const result = InitDataValidator.validate(initData, botToken);
if (!result.valid) {
  // Diagnose private chat issue
  const diagnosis = InitDataValidator.diagnoseMissingInitData(window.Telegram);
  console.log(diagnosis.explanation);
  console.log(diagnosis.workarounds);
}
```

#### 4. TelegramDebugger
```typescript
import { telegramDebug } from './utils/enhancedDebug';

// Full Telegram diagnostics
telegramDebug.logInitData(window.Telegram);

// Auth events
telegramDebug.logAuthEvent('authenticating');
telegramDebug.logAuthError(error, { context: 'login' });

// API calls
telegramDebug.logApiCall('POST', '/auth/token', data);
telegramDebug.logApiResponse('POST', '/auth/token', 200, response);

// WebSocket
telegramDebug.logWebSocketEvent('connected');
telegramDebug.logWebSocketError(error);
```

#### 5. KeyboardValidator
```typescript
import { KeyboardValidator } from './utils/enhancedDebug';

const { valid, issues } = KeyboardValidator.validate(buttons);
if (!valid) {
  console.error('Keyboard issues:', issues);
  // e.g., ["Row 0, Button 1: callback_data exceeds 64 bytes (72 bytes)"]
}
```

## Error Codes Reference

### Authentication Errors
- `MISSING_INIT_DATA` - No initData from Telegram
- `HASH_MISMATCH` - Hash validation failed
- `EXPIRED_INIT_DATA` - Data older than 24 hours
- `AUTH_FAILED` - General authentication failure
- `TOKEN_EXPIRED` - JWT token expired
- `NOT_IN_ANY_GROUP` - User not member of any groups

### Group Errors
- `GROUP_NOT_FOUND` - Group doesn't exist
- `GROUP_LOAD_FAILED` - API error fetching group
- `GROUP_ACCESS_DENIED` - User lacks permissions

### WebSocket Errors
- `WS_CONNECTION_FAILED` - Could not establish connection
- `WS_CLOSED_UNEXPECTEDLY` - Abnormal closure (code 1006)
- `WS_MESSAGE_PARSE_ERROR` - Invalid JSON received

### Telegram API Errors
- `BOT_BLOCKED` - User blocked the bot
- `CHAT_NOT_FOUND` - Invalid chat ID
- `NOT_ENOUGH_RIGHTS` - Missing admin permissions
- `USER_IS_ADMIN` - Cannot restrict another admin
- `CALLBACK_DATA_TOO_LONG` - Exceeds 64 bytes
- `CALLBACK_QUERY_TOO_OLD` - Older than 15 minutes

## Environment Variables

### Bot (Python)
```bash
# Enable debug logging
NEXUS_DEBUG=true

# Verbose output (includes file locations)
NEXUS_DEBUG_VERBOSE=true
```

### Mini App (TypeScript)
```bash
# In .env or build config
VITE_DEBUG_VERBOSE=true
```

## Common Issues & Fixes

### 1. "Missing initData in private chats"

**Problem**: Telegram WebApp in private chats often doesn't include initData.

**Diagnosis**:
```typescript
const diagnosis = InitDataValidator.diagnoseMissingInitData(window.Telegram);
// Returns:
// {
//   inTelegram: true,
//   chatType: 'private',
//   explanation: 'Mini App opened from private chat...',
//   workarounds: ['Open from a group', ...]
// }
```

**Fix**: Open Mini App from a group where bot is a member.

### 2. "Hash validation failures"

**Problem**: initData hash doesn't match computed hash.

**Causes**:
1. Wrong bot token used for validation
2. initData was modified after signing
3. URL encoding issues

**Diagnosis**:
```python
result = InitDataValidator.validate(init_data, bot_token)
print(result["diagnostics"]["computed_hash_prefix"])
print(result["diagnostics"]["received_hash_prefix"])
```

**Fix**: Ensure the token matches the bot that opened the Mini App.

### 3. "Commands not working"

**Diagnosis**:
```python
CommandDebugger.log_command_received(ctx, command, args)
CommandDebugger.log_permission_check(ctx, command, required_role, has_perm)
```

**Common fixes**:
- Check bot has admin rights in group
- Verify command is enabled for the group
- Check user has required role

### 4. "Inline keyboards not working"

**Diagnosis**:
```typescript
const { valid, issues } = KeyboardValidator.validate(buttons);
```

**Common issues**:
- callback_data exceeds 64 bytes
- Button text is empty
- URL format is invalid

### 5. "WebSocket connection problems"

**Diagnosis**: Check close code in debug logs
- 1006: Abnormal closure - check network/server
- 1011: Server error - check server logs
- 1008: Policy violation - check auth token

## Debug Report Generation

### Bot (Python)
```python
from bot.core.debug_logger import debug

# Generate diagnostic report
report = debug.generate_diagnostic_report()
print(report)

# Export logs
logs = debug.export_logs(level=LogLevel.ERROR, last_n=100)
print(logs)

# Get recent errors
errors = debug.get_recent_errors(n=10)
for entry in errors:
    print(f"[{entry.timestamp}] {entry.message}")
    print(f"  Fix: {entry.fix_suggestion}")
```

### Mini App (TypeScript)
```typescript
import { enhancedDebug } from './utils/enhancedDebug';

// Generate report
const report = enhancedDebug.generateReport();
console.log(report);

// Export all logs
const logs = enhancedDebug.export();
localStorage.setItem('debug_logs', logs);

// Subscribe to new entries
const unsubscribe = enhancedDebug.subscribe((entries) => {
  console.log(`Total entries: ${entries.length}`);
});
```

## Integration Examples

### Adding debug to a new module

**Python**:
```python
from bot.core.debug_logger import debug, debug_decorator, DebugContext

@debug_decorator("my_module")
async def my_handler(ctx):
    with DebugContext("my_operation", "my_module") as dbg:
        dbg.log_step("step1")
        result = await do_work()
        dbg.add_data("result", result)
        return result
```

**TypeScript**:
```typescript
import { enhancedDebug, LogCategory } from '../utils/enhancedDebug';

async function myHandler() {
  return enhancedDebug.withContext('myOperation', LogCategory.API, async (ctx) => {
    ctx.log('Starting operation');
    const result = await doWork();
    ctx.log('Operation complete');
    return result;
  });
}
```

## Performance Monitoring

### Bot
```python
from bot.core.debug_logger import debug

# Track performance
debug.track_performance("database_query", duration_ms=45.2)

# Get stats
stats = debug.get_performance_stats("database_query")
print(stats)
# {"count": 100, "avg_ms": 42.5, "min_ms": 20.0, "max_ms": 150.0}
```

### Mini App
```typescript
// Automatic tracking
const result = await enhancedDebug.track('apiCall', async () => {
  return await fetch('/api/data');
}, { endpoint: '/api/data' });

// Get stats
const stats = enhancedDebug.getPerformanceStats('apiCall');
console.log(stats);
// { count: 50, avgMs: 120, minMs: 80, maxMs: 300, successRate: 98 }
```

## Summary

The Nexus Debug System provides:

1. **Instant diagnostics** for all common errors
2. **Actionable fix suggestions** with every error
3. **Full context capture** for debugging
4. **Performance tracking** for optimization
5. **Backward compatibility** with existing debug code
6. **100k+ line output capability** with efficient circular buffer
7. **Export capabilities** for troubleshooting

Enable `NEXUS_DEBUG=true` to start using the full debug system!
