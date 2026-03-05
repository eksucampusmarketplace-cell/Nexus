"""
Nexus Debug Logger - Comprehensive Debugging & Diagnostics System

Provides sophisticated debugging capabilities for the Telegram bot with:
- 100k+ line debug output capability
- Automatic error analysis and fix suggestions
- Full context capture for every operation
- Performance monitoring
- Telegram API error decoding
- initData validation
- Command flow tracing
- Inline keyboard diagnostics

Usage:
    from bot.core.debug_logger import debug, DebugContext, ErrorAnalyzer

    # Basic logging
    debug.info("Starting module", module="captcha")

    # Context-based logging with automatic error analysis
    with DebugContext("command_handler", command="warn") as ctx:
        await handle_warn(ctx, message)
        ctx.success("User warned successfully")

    # Error with automatic fix suggestion
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        debug.error("Failed to send message", error=e, chat_id=chat_id)
        fix = ErrorAnalyzer.suggest_fix(e)
        debug.fix_suggestion(fix)
"""

import asyncio
import functools
import hashlib
import hmac
import inspect
import json
import logging
import os
import sys
import time
import traceback
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, Type

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, Update, User

# Configure main logger
logging.basicConfig(
    level=logging.DEBUG if os.getenv("NEXUS_DEBUG", "false").lower() == "true" else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)


class LogLevel(Enum):
    """Extended log levels for granular debugging."""
    TRACE = "TRACE"      # Ultra-detailed tracing
    DEBUG = "DEBUG"      # Detailed debugging
    INFO = "INFO"        # General information
    SUCCESS = "SUCCESS"  # Successful operations
    WARN = "WARN"        # Warnings
    ERROR = "ERROR"      # Errors
    CRITICAL = "CRITICAL"  # Critical failures
    FIX = "FIX"          # Fix suggestions


class ErrorCategory(Enum):
    """Categories of errors for better diagnosis."""
    TELEGRAM_API = "telegram_api"
    DATABASE = "database"
    REDIS = "redis"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


@dataclass
class DebugEntry:
    """A single debug log entry."""
    timestamp: datetime
    level: LogLevel
    component: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    fix_suggestion: Optional[str] = None
    file_location: Optional[str] = None
    line_number: Optional[int] = None
    function: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "component": self.component,
            "message": self.message,
            "context": self.context,
            "stack_trace": self.stack_trace,
            "fix_suggestion": self.fix_suggestion,
            "file_location": self.file_location,
            "line_number": self.line_number,
            "function": self.function,
        }


@dataclass
class TelegramContext:
    """Captures complete Telegram context for debugging."""
    update_id: Optional[int] = None
    message_id: Optional[int] = None
    chat_id: Optional[int] = None
    chat_type: Optional[str] = None
    chat_title: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_bot: bool = False
    message_text: Optional[str] = None
    command: Optional[str] = None
    callback_data: Optional[str] = None
    bot_username: Optional[str] = None
    init_data: Optional[str] = None
    init_data_valid: Optional[bool] = None
    hash_validation_error: Optional[str] = None

    @classmethod
    def from_update(cls, update: Update, bot: Optional[Bot] = None, bot_username: Optional[str] = None) -> "TelegramContext":
        """Extract context from a Telegram update."""
        ctx = cls()
        ctx.update_id = update.update_id

        if bot_username:
            ctx.bot_username = bot_username
        elif bot:
            # Bot object doesn't have username attribute directly
            # Username should be passed via bot_username parameter from BotIdentity
            ctx.bot_username = getattr(bot, 'username', None)

        if update.message:
            msg = update.message
            ctx.message_id = msg.message_id
            ctx.message_text = msg.text
            ctx.chat_id = msg.chat.id
            ctx.chat_type = msg.chat.type
            ctx.chat_title = getattr(msg.chat, 'title', None)

            if msg.from_user:
                ctx.user_id = msg.from_user.id
                ctx.username = msg.from_user.username
                ctx.first_name = msg.from_user.first_name
                ctx.is_bot = msg.from_user.is_bot

            if msg.text and msg.text.startswith('/'):
                ctx.command = msg.text.split()[0].split('@')[0].lower()

        elif update.callback_query:
            cq = update.callback_query
            ctx.callback_data = cq.data
            ctx.message_id = cq.message.message_id if cq.message else None
            ctx.chat_id = cq.message.chat.id if cq.message else None
            ctx.chat_type = cq.message.chat.type if cq.message else None

            if cq.from_user:
                ctx.user_id = cq.from_user.id
                ctx.username = cq.from_user.username

        return ctx

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ErrorAnalyzer:
    """Analyzes errors and provides actionable fix suggestions."""

    TELEGRAM_ERROR_PATTERNS = {
        "bot was blocked by the user": {
            "category": ErrorCategory.PERMISSION,
            "fix": "User has blocked the bot. Cannot send messages to this user. Consider checking user status before sending DMs.",
            "code": "USER_BLOCKED"
        },
        "chat not found": {
            "category": ErrorCategory.TELEGRAM_API,
            "fix": "The chat ID does not exist or the bot is not a member. Verify the chat ID and ensure bot has been added to the group/channel.",
            "code": "CHAT_NOT_FOUND"
        },
        "message is not modified": {
            "category": ErrorCategory.VALIDATION,
            "fix": "Attempted to edit a message with identical content. Check if content has actually changed before editing.",
            "code": "MESSAGE_NOT_MODIFIED"
        },
        "message to edit not found": {
            "category": ErrorCategory.TELEGRAM_API,
            "fix": "The message you're trying to edit has been deleted or the ID is incorrect. Verify the message ID.",
            "code": "MESSAGE_NOT_FOUND"
        },
        "message can't be deleted": {
            "category": ErrorCategory.PERMISSION,
            "fix": "Bot lacks permission to delete messages or message is too old (>48h). Check bot permissions in group settings.",
            "code": "CANT_DELETE_MESSAGE"
        },
        "not enough rights": {
            "category": ErrorCategory.PERMISSION,
            "fix": "Bot lacks required permissions. Go to group settings -> Administrators -> Nexus Bot and enable all required permissions (Delete messages, Restrict members, Pin messages, etc.).",
            "code": "NOT_ENOUGH_RIGHTS"
        },
        "user is an administrator": {
            "category": ErrorCategory.AUTHORIZATION,
            "fix": "Cannot restrict/ban an admin. The target user has admin privileges. Demote them first or use a different approach.",
            "code": "USER_IS_ADMIN"
        },
        "user not found": {
            "category": ErrorCategory.TELEGRAM_API,
            "fix": "The specified user ID is invalid or the user hasn't interacted with the bot. Verify the user ID.",
            "code": "USER_NOT_FOUND"
        },
        "retry after": {
            "category": ErrorCategory.RATE_LIMIT,
            "fix": "Rate limit hit. Implement exponential backoff and retry after the specified delay. Consider reducing message frequency.",
            "code": "RETRY_AFTER"
        },
        "invalid bot token": {
            "category": ErrorCategory.AUTHENTICATION,
            "fix": "The bot token is invalid or revoked. Check BOT_TOKEN environment variable and get a new token from @BotFather if needed.",
            "code": "INVALID_TOKEN"
        },
        "init data is invalid": {
            "category": ErrorCategory.VALIDATION,
            "fix": "Telegram initData validation failed. This usually means: 1) Data was tampered with, 2) Wrong bot token used for validation, 3) Data is expired (>24h old). Check your bot token matches the one from @BotFather.",
            "code": "INVALID_INIT_DATA"
        },
        "hash mismatch": {
            "category": ErrorCategory.VALIDATION,
            "fix": "Hash validation failed for initData. Ensure: 1) You're using the correct bot token, 2) initData hasn't been modified, 3) URL parameters are properly encoded. The token used for validation MUST match the bot that opened the Mini App.",
            "code": "HASH_MISMATCH"
        },
        "inline keyboard": {
            "category": ErrorCategory.VALIDATION,
            "fix": "Inline keyboard validation failed. Check: 1) callback_data must be 1-64 bytes, 2) Button text must be non-empty, 3) URL buttons need valid URLs, 4) Max 100 buttons total.",
            "code": "INVALID_KEYBOARD"
        },
        "query is too old": {
            "category": ErrorCategory.TIMEOUT,
            "fix": "Callback query is older than 15 minutes. Telegram requires callback queries to be answered within 15 minutes. Answer queries immediately or implement timeout handling.",
            "code": "QUERY_TOO_OLD"
        },
        "button_url_invalid": {
            "category": ErrorCategory.VALIDATION,
            "fix": "Invalid URL in inline keyboard button. URLs must: 1) Start with http:// or https://, 2) Be properly encoded, 3) Not exceed certain length limits.",
            "code": "INVALID_BUTTON_URL"
        },
        "can't parse entities": {
            "category": ErrorCategory.VALIDATION,
            "fix": "HTML/Markdown parsing error. Check: 1) All tags are properly closed, 2) No unsupported tags used, 3) Special characters like < > & are escaped if not part of tags, 4) Nested tags are valid.",
            "code": "PARSE_ERROR"
        },
        "message is too long": {
            "category": ErrorCategory.VALIDATION,
            "fix": "Message exceeds 4096 characters limit. Split the message into multiple parts or use a document/file for long content.",
            "code": "MESSAGE_TOO_LONG"
        },
        "BUTTON_DATA_INVALID": {
            "category": ErrorCategory.VALIDATION,
            "fix": "Callback data exceeds 64 bytes or contains invalid characters. Keep callback_data short. Use prefixes and store full data in Redis/database.",
            "code": "BUTTON_DATA_INVALID"
        },
    }

    @classmethod
    def analyze(cls, error: Exception, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze an error and return detailed diagnostic information."""
        error_str = str(error).lower()
        error_type = type(error).__name__

        result = {
            "original_error": str(error),
            "error_type": error_type,
            "category": ErrorCategory.UNKNOWN,
            "code": "UNKNOWN",
            "fix": "No specific fix available. Check the full error traceback.",
            "context": context or {},
            "telegram_specific": False,
        }

        # Check Telegram-specific patterns
        for pattern, info in cls.TELEGRAM_ERROR_PATTERNS.items():
            if pattern in error_str:
                result.update(info)
                result["telegram_specific"] = True
                return result

        # Check exception type for Telegram errors
        if isinstance(error, TelegramBadRequest):
            result["category"] = ErrorCategory.VALIDATION
            result["code"] = "BAD_REQUEST"
            result["fix"] = "Bad request to Telegram API. Check all parameters are valid and formatted correctly."
        elif isinstance(error, TelegramForbiddenError):
            result["category"] = ErrorCategory.PERMISSION
            result["code"] = "FORBIDDEN"
            result["fix"] = "Bot lacks permission. Check bot is admin with required permissions in the group."
        elif isinstance(error, TelegramNotFound):
            result["category"] = ErrorCategory.TELEGRAM_API
            result["code"] = "NOT_FOUND"
            result["fix"] = "Resource not found. Chat, message, or user may not exist."
        elif isinstance(error, TelegramRetryAfter):
            retry_after = getattr(error, 'retry_after', 'unknown')
            result["category"] = ErrorCategory.RATE_LIMIT
            result["code"] = "RATE_LIMITED"
            result["fix"] = f"Rate limited by Telegram. Wait {retry_after} seconds before retrying."
        elif isinstance(error, TelegramServerError):
            result["category"] = ErrorCategory.NETWORK
            result["code"] = "SERVER_ERROR"
            result["fix"] = "Telegram server error. Retry with exponential backoff."
        elif isinstance(error, TelegramUnauthorizedError):
            result["category"] = ErrorCategory.AUTHENTICATION
            result["code"] = "UNAUTHORIZED"
            result["fix"] = "Bot token is invalid. Get a valid token from @BotFather."

        return result

    @classmethod
    def suggest_fix(cls, error: Exception) -> str:
        """Get a human-readable fix suggestion."""
        analysis = cls.analyze(error)
        return f"[{analysis['code']}] {analysis['fix']}"


class InitDataValidator:
    """Validates Telegram Mini App initData with detailed diagnostics."""

    @staticmethod
    def validate(init_data: str, bot_token: str) -> Dict[str, Any]:
        """
        Validate initData and return detailed diagnostic information.

        Returns:
            Dict with validation results and detailed diagnostics
        """
        result = {
            "valid": False,
            "init_data_present": bool(init_data),
            "init_data_length": len(init_data) if init_data else 0,
            "bot_token_present": bool(bot_token),
            "bot_token_length": len(bot_token) if bot_token else 0,
            "parsed_params": {},
            "errors": [],
            "warnings": [],
            "diagnostics": {},
        }

        if not init_data:
            result["errors"].append("initData is empty or None")
            result["diagnostics"]["cause"] = "MISSING_INIT_DATA"
            result["diagnostics"]["explanation"] = (
                "No initData was received from Telegram WebApp. "
                "This happens when: 1) Opening Mini App from private chat instead of group, "
                "2) Not using Telegram WebApp (direct browser access), "
                "3) WebApp not properly initialized. "
                "FIX: Always open Mini App from a group where bot is a member."
            )
            return result

        if not bot_token:
            result["errors"].append("Bot token is empty or None")
            result["diagnostics"]["cause"] = "MISSING_BOT_TOKEN"
            return result

        # Parse initData
        try:
            parsed = {}
            for pair in init_data.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    parsed[key] = value
            result["parsed_params"] = {k: v[:50] + '...' if len(v) > 50 else v
                                        for k, v in parsed.items()}
        except Exception as e:
            result["errors"].append(f"Failed to parse initData: {e}")
            return result

        # Check required fields
        if 'hash' not in parsed:
            result["errors"].append("Missing 'hash' parameter in initData")
            result["diagnostics"]["cause"] = "MISSING_HASH"
            result["diagnostics"]["explanation"] = (
                "initData is missing the required 'hash' field. "
                "This should never happen with legitimate Telegram WebApp. "
                "The data may be malformed or tampered with."
            )
            return result

        # Validate hash
        try:
            received_hash = parsed.pop('hash')
            data_check_string = '\n'.join(
                f"{k}={v}" for k, v in sorted(parsed.items())
            )

            secret_key = hmac.new(
                key=b"WebAppData",
                msg=bot_token.encode(),
                digestmod=hashlib.sha256
            ).digest()

            computed_hash = hmac.new(
                key=secret_key,
                msg=data_check_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()

            result["diagnostics"]["computed_hash_prefix"] = computed_hash[:16]
            result["diagnostics"]["received_hash_prefix"] = received_hash[:16]
            result["diagnostics"]["data_check_string_length"] = len(data_check_string)

            if hmac.compare_digest(computed_hash, received_hash):
                result["valid"] = True
            else:
                result["errors"].append("Hash mismatch - data may be tampered with or wrong bot token")
                result["diagnostics"]["cause"] = "HASH_MISMATCH"
                result["diagnostics"]["explanation"] = (
                    "The computed hash doesn't match the received hash. "
                    "This usually means: 1) Wrong bot token used for validation, "
                    "2) initData was modified after being signed by Telegram, "
                    "3) URL encoding issues. "
                    "FIX: Ensure BOT_TOKEN matches the bot that opened the Mini App. "
                    "If using multiple bots, validate against the correct token based on user membership."
                )

        except Exception as e:
            result["errors"].append(f"Hash validation error: {e}")
            result["diagnostics"]["cause"] = "VALIDATION_ERROR"

        # Check auth_date
        if 'auth_date' in parsed:
            try:
                auth_date = int(parsed['auth_date'])
                current_time = int(time.time())
                age_seconds = current_time - auth_date
                result["diagnostics"]["auth_age_seconds"] = age_seconds
                result["diagnostics"]["auth_age_hours"] = round(age_seconds / 3600, 2)

                if age_seconds > 86400:  # 24 hours
                    result["warnings"].append(f"initData is {age_seconds // 3600} hours old (may be expired)")
            except ValueError:
                result["warnings"].append("Invalid auth_date format")

        return result

    @staticmethod
    def diagnose_private_chat_issue(init_data: Optional[str], telegram_webapp: Any) -> Dict[str, Any]:
        """
        Diagnose why initData is missing in private chats.

        This is a common issue - Telegram WebApp in private chats often
        doesn't include initData in the same way as in groups.
        """
        diagnosis = {
            "issue": "MISSING_INITDATA_PRIVATE_CHAT",
            "is_private_chat": False,
            "explanation": "",
            "workarounds": [],
            "checks": {},
        }

        if not telegram_webapp:
            diagnosis["explanation"] = "Telegram WebApp object not available. Not running in Telegram."
            diagnosis["checks"]["in_telegram"] = False
            return diagnosis

        diagnosis["checks"]["in_telegram"] = True
        diagnosis["checks"]["webapp_version"] = getattr(telegram_webapp, 'version', 'unknown')
        diagnosis["checks"]["platform"] = getattr(telegram_webapp, 'platform', 'unknown')

        init_data_unsafe = getattr(telegram_webapp, 'initDataUnsafe', {})
        if init_data_unsafe:
            chat = init_data_unsafe.get('chat')
            if chat:
                chat_type = chat.get('type')
                diagnosis["checks"]["chat_type"] = chat_type
                if chat_type == 'private':
                    diagnosis["is_private_chat"] = True
                    diagnosis["explanation"] = (
                        "Mini App opened from private chat with bot. "
                        "Telegram WebApp may not provide full initData in private chats. "
                        "This is expected behavior - initData is primarily for group context."
                    )
                    diagnosis["workarounds"] = [
                        "Open Mini App from a group where bot is a member",
                        "Use deep linking with start_param to pass context",
                        "Implement alternative auth (JWT tokens) for private chat usage",
                        "Use localStorage to maintain session across opens",
                    ]

        if not init_data:
            diagnosis["explanation"] += "\n\nNo initData string available. This means:"
            diagnosis["explanation"] += "\n1. WebApp.initData is empty (common in private chats)"
            diagnosis["explanation"] += "\n2. Mini App was opened without proper context"

        return diagnosis


class DebugLogger:
    """
    Sophisticated debug logger with comprehensive diagnostics.

    Features:
    - Circular buffer for recent logs (memory-efficient)
    - Performance tracking
    - Full context capture
    - Automatic error analysis
    - Export capabilities
    """

    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.entries: deque = deque(maxlen=max_entries)
        self.performance_counters: Dict[str, List[float]] = {}
        self.component_stats: Dict[str, Dict[str, int]] = {}
        self._lock = asyncio.Lock()
        self._enabled = os.getenv("NEXUS_DEBUG", "true").lower() == "true"
        self._verbose = os.getenv("NEXUS_DEBUG_VERBOSE", "false").lower() == "true"

        # Internal logger
        self._logger = logging.getLogger("nexus.debug")

    def _get_caller_info(self) -> Tuple[str, int, str]:
        """Get information about the calling code."""
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the caller (skip this method and the public method)
            for _ in range(3):
                frame = frame.f_back if frame else None
            if frame:
                filename = os.path.basename(frame.f_code.co_filename)
                lineno = frame.f_lineno
                function = frame.f_code.co_name
                return filename, lineno, function
        finally:
            del frame
        return "unknown", 0, "unknown"

    def _log(self, level: LogLevel, component: str, message: str,
             context: Optional[Dict] = None, error: Optional[Exception] = None):
        """Internal logging method."""
        if not self._enabled and level not in (LogLevel.ERROR, LogLevel.CRITICAL):
            return

        file_location, line_number, function = self._get_caller_info()

        entry = DebugEntry(
            timestamp=datetime.utcnow(),
            level=level,
            component=component,
            message=message,
            context=context or {},
            file_location=file_location,
            line_number=line_number,
            function=function,
        )

        if error:
            entry.stack_trace = traceback.format_exc()
            analysis = ErrorAnalyzer.analyze(error, context)
            entry.fix_suggestion = analysis["fix"]
            entry.context["error_analysis"] = analysis

        # Add to buffer
        self.entries.append(entry)

        # Update stats
        if component not in self.component_stats:
            self.component_stats[component] = {"total": 0, "errors": 0}
        self.component_stats[component]["total"] += 1
        if level in (LogLevel.ERROR, LogLevel.CRITICAL):
            self.component_stats[component]["errors"] += 1

        # Console output
        self._output_to_console(entry)

    def _output_to_console(self, entry: DebugEntry):
        """Output entry to console with formatting."""
        level_colors = {
            LogLevel.TRACE: "\033[90m",    # Gray
            LogLevel.DEBUG: "\033[36m",    # Cyan
            LogLevel.INFO: "\033[34m",     # Blue
            LogLevel.SUCCESS: "\033[32m",  # Green
            LogLevel.WARN: "\033[33m",     # Yellow
            LogLevel.ERROR: "\033[31m",    # Red
            LogLevel.CRITICAL: "\033[35m", # Magenta
            LogLevel.FIX: "\033[92m",      # Bright Green
        }
        reset = "\033[0m"

        color = level_colors.get(entry.level, "")
        location = f"{entry.file_location}:{entry.line_number}"

        log_line = (
            f"{color}[{entry.level.value}]{reset} "
            f"\033[90m[{entry.timestamp.strftime('%H:%M:%S.%f')[:-3]}]{reset} "
            f"\033[95m[{entry.component}]{reset} "
            f"{entry.message}"
        )

        if self._verbose:
            log_line += f" \033[90m({location} in {entry.function}){reset}"

        if entry.context:
            context_str = json.dumps(entry.context, default=str, indent=2)[:500]
            log_line += f"\n  Context: {context_str}"

        if entry.fix_suggestion:
            log_line += f"\n  \033[92m💡 FIX: {entry.fix_suggestion}{reset}"

        if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL) and entry.stack_trace:
            # Only show last few lines of stack trace in console
            lines = entry.stack_trace.strip().split('\n')
            if len(lines) > 5:
                log_line += f"\n  \033[90m... ({len(lines)} lines)"
                log_line += f"\n  {chr(10).join(lines[-5:])}{reset}"
            else:
                log_line += f"\n  \033[90m{entry.stack_trace}{reset}"

        print(log_line)

        # Also log to standard logger
        std_level = logging.INFO
        if entry.level == LogLevel.ERROR:
            std_level = logging.ERROR
        elif entry.level == LogLevel.CRITICAL:
            std_level = logging.CRITICAL
        elif entry.level == LogLevel.WARN:
            std_level = logging.WARNING
        elif entry.level == LogLevel.DEBUG:
            std_level = logging.DEBUG

        self._logger.log(std_level, f"[{entry.component}] {entry.message}")

    # Public API
    def trace(self, message: str, component: str = "general", **context):
        """Ultra-detailed trace logging."""
        self._log(LogLevel.TRACE, component, message, context)

    def debug(self, message: str, component: str = "general", **context):
        """Detailed debug logging."""
        self._log(LogLevel.DEBUG, component, message, context)

    def info(self, message: str, component: str = "general", **context):
        """General information logging."""
        self._log(LogLevel.INFO, component, message, context)

    def success(self, message: str, component: str = "general", **context):
        """Success logging."""
        self._log(LogLevel.SUCCESS, component, message, context)

    def warn(self, message: str, component: str = "general", **context):
        """Warning logging."""
        self._log(LogLevel.WARN, component, message, context)

    def error(self, message: str, error: Optional[Exception] = None,
              component: str = "general", **context):
        """Error logging with automatic analysis."""
        self._log(LogLevel.ERROR, component, message, context, error)

    def critical(self, message: str, error: Optional[Exception] = None,
                 component: str = "general", **context):
        """Critical error logging."""
        self._log(LogLevel.CRITICAL, component, message, context, error)

    def fix_suggestion(self, suggestion: str, component: str = "general"):
        """Log a fix suggestion."""
        self._log(LogLevel.FIX, component, f"SUGGESTION: {suggestion}")

    def track_performance(self, operation: str, duration_ms: float):
        """Track performance of an operation."""
        if operation not in self.performance_counters:
            self.performance_counters[operation] = []
        self.performance_counters[operation].append(duration_ms)

        # Keep only last 100 measurements
        if len(self.performance_counters[operation]) > 100:
            self.performance_counters[operation].pop(0)

    def get_performance_stats(self, operation: str) -> Optional[Dict]:
        """Get performance statistics for an operation."""
        times = self.performance_counters.get(operation, [])
        if not times:
            return None

        return {
            "count": len(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "recent_avg_ms": sum(times[-10:]) / min(len(times), 10),
        }

    def export_logs(self, level: Optional[LogLevel] = None,
                    component: Optional[str] = None,
                    last_n: Optional[int] = None) -> str:
        """Export logs as formatted text."""
        entries = list(self.entries)

        if level:
            entries = [e for e in entries if e.level == level]
        if component:
            entries = [e for e in entries if e.component == component]
        if last_n:
            entries = entries[-last_n:]

        lines = []
        lines.append("=" * 80)
        lines.append("NEXUS DEBUG LOG EXPORT")
        lines.append(f"Generated: {datetime.utcnow().isoformat()}")
        lines.append(f"Total entries: {len(entries)}")
        lines.append("=" * 80)
        lines.append("")

        for entry in entries:
            lines.append(f"[{entry.timestamp.isoformat()}] [{entry.level.value}] [{entry.component}]")
            lines.append(f"  Message: {entry.message}")
            lines.append(f"  Location: {entry.file_location}:{entry.line_number} in {entry.function}")
            if entry.context:
                lines.append(f"  Context: {json.dumps(entry.context, default=str, indent=4)}")
            if entry.fix_suggestion:
                lines.append(f"  Fix: {entry.fix_suggestion}")
            if entry.stack_trace:
                lines.append(f"  Stack Trace:\n{entry.stack_trace}")
            lines.append("")

        return "\n".join(lines)

    def get_recent_errors(self, n: int = 10) -> List[DebugEntry]:
        """Get recent error entries."""
        errors = [e for e in self.entries if e.level in (LogLevel.ERROR, LogLevel.CRITICAL)]
        return list(errors)[-n:]

    def generate_diagnostic_report(self) -> str:
        """Generate a comprehensive diagnostic report."""
        lines = []
        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + " NEXUS BOT DIAGNOSTIC REPORT ".center(78) + "║")
        lines.append("╚" + "═" * 78 + "╝")
        lines.append("")
        lines.append(f"Generated: {datetime.utcnow().isoformat()}")
        lines.append(f"Debug Mode: {'ENABLED' if self._enabled else 'DISABLED'}")
        lines.append(f"Total Log Entries: {len(self.entries)}")
        lines.append("")

        # Component stats
        lines.append("┌" + "─" * 78 + "┐")
        lines.append("│ COMPONENT STATISTICS".ljust(79) + "│")
        lines.append("├" + "─" * 78 + "┤")
        for component, stats in sorted(self.component_stats.items()):
            error_rate = (stats['errors'] / stats['total'] * 100) if stats['total'] > 0 else 0
            lines.append(f"│ {component:<30} Total: {stats['total']:>5}  Errors: {stats['errors']:>4} ({error_rate:>5.1f}%)".ljust(79) + "│")
        lines.append("└" + "─" * 78 + "┘")
        lines.append("")

        # Performance stats
        if self.performance_counters:
            lines.append("┌" + "─" * 78 + "┐")
            lines.append("│ PERFORMANCE STATISTICS".ljust(79) + "│")
            lines.append("├" + "─" * 78 + "┤")
            for operation, stats in sorted(self.get_performance_stats(op).items() for op in self.performance_counters):
                if stats:
                    lines.append(f"│ {operation:<30} Avg: {stats['avg_ms']:>6.2f}ms  Min: {stats['min_ms']:>6.2f}ms  Max: {stats['max_ms']:>6.2f}ms".ljust(79) + "│")
            lines.append("└" + "─" * 78 + "┘")
            lines.append("")

        # Recent errors
        recent_errors = self.get_recent_errors(5)
        if recent_errors:
            lines.append("┌" + "─" * 78 + "┐")
            lines.append("│ RECENT ERRORS".ljust(79) + "│")
            lines.append("├" + "─" * 78 + "┤")
            for entry in recent_errors:
                lines.append(f"│ [{entry.timestamp.strftime('%H:%M:%S')}] {entry.component}".ljust(79) + "│")
                lines.append(f"│   {entry.message[:74]}".ljust(79) + "│")
                if entry.fix_suggestion:
                    lines.append(f"│   💡 {entry.fix_suggestion[:70]}".ljust(79) + "│")
                lines.append("│".ljust(79) + "│")
            lines.append("└" + "─" * 78 + "┘")

        return "\n".join(lines)


# Global debug instance
debug = DebugLogger()


class DebugContext:
    """
    Context manager for debugging operations with automatic timing and error handling.

    Usage:
        with DebugContext("command_handler", command="warn", user_id=123) as ctx:
            await handle_command(message)
            ctx.add_data("result", "success")
    """

    def __init__(self, operation: str, component: str = "general", **initial_context):
        self.operation = operation
        self.component = component
        self.context = initial_context
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.success = False
        self.error: Optional[Exception] = None

    def __enter__(self):
        self.start_time = time.time()
        debug.trace(f"Starting: {self.operation}", self.component, **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000

        debug.track_performance(self.operation, duration_ms)

        if exc_val:
            self.error = exc_val
            debug.error(
                f"Failed: {self.operation} ({duration_ms:.2f}ms)",
                error=exc_val,
                component=self.component,
                duration_ms=duration_ms,
                **self.context
            )
            return False  # Don't suppress exception

        debug.success(
            f"Completed: {self.operation} ({duration_ms:.2f}ms)",
            self.component,
            duration_ms=duration_ms,
            **self.context
        )
        self.success = True
        return True

    def add_data(self, key: str, value: Any):
        """Add data to the context."""
        self.context[key] = value

    def log_step(self, step: str, **data):
        """Log an intermediate step."""
        self.context.update(data)
        debug.debug(f"Step: {self.operation}.{step}", self.component, **self.context)


def debug_decorator(component: str = None, log_args: bool = True, log_result: bool = False):
    """
    Decorator for debugging function calls.

    Usage:
        @debug_decorator("moderation")
        async def ban_user(ctx, user_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        comp = component or func.__module__.split('.')[-2] if '.' in func.__module__ else "general"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            context = {}

            if log_args:
                context["args_count"] = len(args)
                context["kwargs_keys"] = list(kwargs.keys())
                # Log specific argument types without full values (privacy)
                for i, arg in enumerate(args[:3]):  # First 3 args only
                    context[f"arg{i}_type"] = type(arg).__name__

            with DebugContext(func_name, comp, **context):
                result = await func(*args, **kwargs)
                if log_result and result is not None:
                    pass  # Result logged in context exit
                return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            context = {}

            if log_args:
                context["args_count"] = len(args)
                context["kwargs_keys"] = list(kwargs.keys())

            with DebugContext(func_name, comp, **context):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class CommandDebugger:
    """Debug utilities for command handling."""

    @staticmethod
    def log_command_received(ctx: Any, command: str, args: List[str]):
        """Log when a command is received."""
        debug.info(
            f"Command received: !{command}",
            "commands",
            command=command,
            args=args,
            user_id=ctx.user.telegram_id if ctx.user else None,
            group_id=ctx.group.telegram_id if ctx.group else None,
            chat_type=ctx.message.chat.type if ctx.message else None,
        )

    @staticmethod
    def log_command_processed(ctx: Any, command: str, success: bool, error: Optional[str] = None):
        """Log command processing result."""
        if success:
            debug.success(f"Command processed: !{command}", "commands", command=command)
        else:
            debug.error(f"Command failed: !{command}", component="commands", error=Exception(error) if error else None)

    @staticmethod
    def log_permission_check(ctx: Any, command: str, required_role: str, has_permission: bool):
        """Log permission checks."""
        user_role = ctx.user.role.value if ctx.user else "none"
        if has_permission:
            debug.debug(f"Permission granted for !{command}", "commands",
                       command=command, user_role=user_role, required=required_role)
        else:
            debug.warn(f"Permission denied for !{command}", "commands",
                      command=command, user_role=user_role, required=required_role,
                      user_id=ctx.user.telegram_id if ctx.user else None)


class KeyboardDebugger:
    """Debug utilities for inline keyboards."""

    @staticmethod
    def validate_keyboard(keyboard: InlineKeyboardMarkup) -> List[str]:
        """Validate keyboard and return list of issues."""
        issues = []

        if not keyboard or not keyboard.inline_keyboard:
            issues.append("Keyboard is empty")
            return issues

        total_buttons = 0
        for row_idx, row in enumerate(keyboard.inline_keyboard):
            for btn_idx, button in enumerate(row):
                total_buttons += 1

                # Check callback_data length (64 bytes max)
                if button.callback_data and len(button.callback_data.encode('utf-8')) > 64:
                    issues.append(
                        f"Row {row_idx}, Button {btn_idx}: callback_data exceeds 64 bytes "
                        f"({len(button.callback_data.encode('utf-8'))} bytes)"
                    )

                # Check button text
                if not button.text or len(button.text.strip()) == 0:
                    issues.append(f"Row {row_idx}, Button {btn_idx}: Empty button text")

                # Check URL validity
                if button.url:
                    if not button.url.startswith(('http://', 'https://', 'tg://')):
                        issues.append(
                            f"Row {row_idx}, Button {btn_idx}: Invalid URL format '{button.url[:30]}'"
                        )

        # Check total button count (100 max)
        if total_buttons > 100:
            issues.append(f"Too many buttons: {total_buttons} (max 100)")

        return issues

    @staticmethod
    def log_keyboard_sent(chat_id: int, keyboard_id: str = None, button_count: int = 0):
        """Log keyboard being sent."""
        debug.debug(f"Sending inline keyboard", "keyboard",
                   chat_id=chat_id, keyboard_id=keyboard_id, button_count=button_count)

    @staticmethod
    def log_callback_received(callback: CallbackQuery):
        """Log callback query received."""
        debug.info(
            "Callback received",
            "keyboard",
            callback_data=callback.data,
            user_id=callback.from_user.id if callback.from_user else None,
            message_id=callback.message.message_id if callback.message else None,
        )


# Export main components
__all__ = [
    "debug",
    "DebugContext",
    "DebugLogger",
    "ErrorAnalyzer",
    "ErrorCategory",
    "InitDataValidator",
    "TelegramContext",
    "CommandDebugger",
    "KeyboardDebugger",
    "debug_decorator",
    "LogLevel",
]
