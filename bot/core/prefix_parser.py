"""Prefix parser for dual prefix command system (! and !!)."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class ParsedCommand:
    """Parsed command from message."""

    is_deactivate: bool  # True if !! prefix (deactivate/remove)
    command: str
    args: List[str]
    duration: Optional[int] = None  # Duration in seconds
    time_range: Optional[Tuple[datetime, datetime]] = None
    is_valid: bool = True


class PrefixParser:
    """
    Parser for the dual prefix command system.

    Handles:
    - !command (activate/execute)
    - !!command (deactivate/remove)
    - /command (standard slash command)
    - Duration parsing: 4, 4m, 4h, 4d, 4w
    - Time parsing: HH:MM
    - Time range parsing: HH:MM HH:MM
    """

    # Duration multipliers in seconds
    DURATION_MULTIPLIERS = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
    }

    # Default duration unit (when just a number is given)
    DEFAULT_DURATION_UNIT = "h"  # Hours

    # Time pattern HH:MM
    TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})$")

    def __init__(self, default_prefix: str = "!"):
        """Initialize parser with configurable prefix."""
        self.default_prefix = default_prefix

    def parse(self, text: str, prefix: str = None) -> Optional[ParsedCommand]:
        """
        Parse a message text for commands.

        Args:
            text: Message text to parse
            prefix: Custom prefix (defaults to !)

        Returns:
            ParsedCommand if command found, None otherwise
        """
        if not text:
            return None

        prefix = prefix or self.default_prefix
        text = text.strip()

        # Check for deactivate prefix (!!)
        deactivate_prefix = prefix * 2
        is_deactivate = text.startswith(deactivate_prefix)

        # Check for activate prefix (!) or slash command
        if is_deactivate:
            command_text = text[len(deactivate_prefix) :].strip()
        elif text.startswith(prefix):
            command_text = text[len(prefix) :].strip()
        elif text.startswith("/"):
            command_text = text[1:].strip()
        else:
            return None

        if not command_text:
            return None

        # Parse command and arguments
        parts = command_text.split()
        if not parts:
            return None

        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Parse duration if present
        duration = None
        time_range = None

        if args:
            # Check for time range (HH:MM HH:MM)
            time_range = self._parse_time_range(args)
            if time_range:
                # Remove time range from args
                args = args[2:]
            else:
                # Check for duration or single time
                duration, args = self._extract_duration(args)

        return ParsedCommand(
            is_deactivate=is_deactivate,
            command=command,
            args=args,
            duration=duration,
            time_range=time_range,
            is_valid=True,
        )

    def _parse_duration(self, value: str) -> Optional[int]:
        """
        Parse a duration string to seconds.

        Supports:
        - Plain number (default unit): 4 -> 4 hours
        - With suffix: 4m, 4h, 4d, 4w
        - Time: 10:00 (returns None, not a duration)
        """
        if not value:
            return None

        value = value.lower().strip()

        # Check if it's a time instead of duration
        if self.TIME_PATTERN.match(value):
            return None

        # Check for suffix
        for suffix, multiplier in self.DURATION_MULTIPLIERS.items():
            if value.endswith(suffix):
                try:
                    num = int(value[:-1])
                    return num * multiplier
                except ValueError:
                    return None

        # Try plain number (use default unit)
        try:
            num = int(value)
            return num * self.DURATION_MULTIPLIERS[self.DEFAULT_DURATION_UNIT]
        except ValueError:
            return None

    def _extract_duration(self, args: List[str]) -> Tuple[Optional[int], List[str]]:
        """
        Extract duration from args and return remaining args.

        Args:
            args: List of arguments

        Returns:
            Tuple of (duration_seconds, remaining_args)
        """
        if not args:
            return None, args

        # First arg might be duration
        first = args[0]
        duration = self._parse_duration(first)

        if duration is not None:
            return duration, args[1:]

        return None, args

    def _parse_time_range(self, args: List[str]) -> Optional[Tuple[datetime, datetime]]:
        """
        Parse time range from args (HH:MM HH:MM).

        Returns:
            Tuple of (start_time, end_time) or None
        """
        if len(args) < 2:
            return None

        time1 = args[0]
        time2 = args[1]

        match1 = self.TIME_PATTERN.match(time1)
        match2 = self.TIME_PATTERN.match(time2)

        if not match1 or not match2:
            return None

        hour1, minute1 = int(match1.group(1)), int(match1.group(2))
        hour2, minute2 = int(match2.group(1)), int(match2.group(2))

        today = datetime.now().date()
        start = datetime.combine(
            today, datetime.min.time().replace(hour=hour1, minute=minute1)
        )
        end = datetime.combine(
            today, datetime.min.time().replace(hour=hour2, minute=minute2)
        )

        return (start, end)

    def parse_time(self, value: str) -> Optional[datetime]:
        """Parse a time string (HH:MM) to datetime today."""
        match = self.TIME_PATTERN.match(value)
        if not match:
            return None

        hour, minute = int(match.group(1)), int(match.group(2))
        today = datetime.now().date()
        return datetime.combine(
            today, datetime.min.time().replace(hour=hour, minute=minute)
        )


# Global parser instance
prefix_parser = PrefixParser()
