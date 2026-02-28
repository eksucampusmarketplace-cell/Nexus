"""
Nexus Bot - Comprehensive Test Script
Tests all implemented modules and commands
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class NexusTestSuite:
    """Test suite for Nexus bot modules."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name: str, condition: bool, message: str = ""):
        """Run a test."""
        result = "✅ PASS" if condition else "❌ FAIL"
        self.tests.append(f"{result} - {name}")
        if message:
            self.tests.append(f"    {message}")

        if condition:
            self.passed += 1
        else:
            self.failed += 1

    def print_results(self):
        """Print test results."""
        print("\n" + "="*60)
        print("NEXUS BOT TEST RESULTS")
        print("="*60)

        for test in self.tests:
            print(test)

        print("\n" + "="*60)
        print(f"Total: {self.passed + self.failed} | Passed: {self.passed} | Failed: {self.failed}")
        print("="*60)

        return self.failed == 0


def test_moderation_module():
    """Test moderation module."""
    print("\n🛡️ Testing Moderation Module...")

    suite = NexusTestSuite()

    # Test command registration
    from bot.modules.moderation import ModerationModule
    module = ModerationModule()

    suite.test(
        "Moderation module loads",
        module.name == "moderation"
    )

    suite.test(
        "Has warn command",
        any(cmd.name == "warn" for cmd in module.commands)
    )

    suite.test(
        "Has mute command",
        any(cmd.name == "mute" for cmd in module.commands)
    )

    suite.test(
        "Has ban command",
        any(cmd.name == "ban" for cmd in module.commands)
    )

    suite.test(
        "Has kick command",
        any(cmd.name == "kick" for cmd in module.commands)
    )

    suite.test(
        "Has trust command",
        any(cmd.name == "trust" for cmd in module.commands)
    )

    suite.test(
        "Has approve command",
        any(cmd.name == "approve" for cmd in module.commands)
    )

    suite.test(
        "Has report command",
        any(cmd.name == "report" for cmd in module.commands)
    )

    suite.print_results()
    return suite.failed == 0


def test_economy_module():
    """Test economy module."""
    print("\n💰 Testing Economy Module...")

    suite = NexusTestSuite()

    from bot.modules.economy import EconomyModule
    module = EconomyModule()

    suite.test(
        "Economy module loads",
        module.name == "economy"
    )

    suite.test(
        "Has balance command",
        any(cmd.name == "balance" for cmd in module.commands)
    )

    suite.test(
        "Has daily command",
        any(cmd.name == "daily" for cmd in module.commands)
    )

    suite.test(
        "Has give command",
        any(cmd.name == "give" for cmd in module.commands)
    )

    suite.test(
        "Has leaderboard command",
        any(cmd.name == "leaderboard" for cmd in module.commands)
    )

    suite.test(
        "Has coinflip command",
        any(cmd.name == "coinflip" for cmd in module.commands)
    )

    suite.test(
        "Has gamble command",
        any(cmd.name == "gamble" for cmd in module.commands)
    )

    suite.test(
        "Has work command",
        any(cmd.name == "work" for cmd in module.commands)
    )

    suite.test(
        "Has crime command",
        any(cmd.name == "crime" for cmd in module.commands)
    )

    suite.test(
        "Has bank command",
        any(cmd.name == "bank" for cmd in module.commands)
    )

    suite.print_results()
    return suite.failed == 0


def test_reputation_module():
    """Test reputation module."""
    print("\n📊 Testing Reputation Module...")

    suite = NexusTestSuite()

    from bot.modules.reputation import ReputationModule
    module = ReputationModule()

    suite.test(
        "Reputation module loads",
        module.name == "reputation"
    )

    suite.test(
        "Has rep command",
        any(cmd.name == "rep" for cmd in module.commands)
    )

    suite.test(
        "Has +rep command",
        any(cmd.name == "+rep" for cmd in module.commands)
    )

    suite.test(
        "Has -rep command",
        any(cmd.name == "-rep" for cmd in module.commands)
    )

    suite.test(
        "Has reputation command",
        any(cmd.name == "reputation" for cmd in module.commands)
    )

    suite.test(
        "Has repleaderboard command",
        any(cmd.name == "repleaderboard" for cmd in module.commands)
    )

    suite.print_results()
    return suite.failed == 0


def test_scheduler_module():
    """Test scheduler module."""
    print("\n📅 Testing Scheduler Module...")

    suite = NexusTestSuite()

    from bot.modules.scheduler import SchedulerModule
    module = SchedulerModule()

    suite.test(
        "Scheduler module loads",
        module.name == "scheduler"
    )

    suite.test(
        "Has schedule command",
        any(cmd.name == "schedule" for cmd in module.commands)
    )

    suite.test(
        "Has recurring command",
        any(cmd.name == "recurring" for cmd in module.commands)
    )

    suite.test(
        "Has listscheduled command",
        any(cmd.name == "listscheduled" for cmd in module.commands)
    )

    suite.test(
        "Has cancelschedule command",
        any(cmd.name == "cancelschedule" for cmd in module.commands)
    )

    # Test time parsing
    suite.test(
        "Parse relative time (30s)",
        module._parse_time("30s") is not None
    )

    suite.test(
        "Parse relative time (5m)",
        module._parse_time("5m") is not None
    )

    suite.test(
        "Parse relative time (2h)",
        module._parse_time("2h") is not None
    )

    suite.test(
        "Parse specific time (14:30)",
        module._parse_time("14:30") is not None
    )

    suite.test(
        "Parse natural time (tomorrow)",
        module._parse_time("tomorrow") is not None
    )

    # Test day parsing
    suite.test(
        "Parse single day (mon)",
        module._parse_days("mon") == [0]
    )

    suite.test(
        "Parse multiple days (mon,wed,fri)",
        set(module._parse_days("mon,wed,fri")) == {0, 2, 4}
    )

    suite.test(
        "Parse day range (mon-fri)",
        set(module._parse_days("mon-fri")) == {0, 1, 2, 3, 4}
    )

    # Test cron parsing
    suite.test(
        "Parse cron expression",
        module._parse_cron("0 9 * * *") is not None
    )

    suite.print_results()
    return suite.failed == 0


def test_other_modules():
    """Test other existing modules."""
    print("\n📦 Testing Other Modules...")

    suite = NexusTestSuite()

    # Test welcome module
    try:
        from bot.modules.welcome import WelcomeModule
        welcome = WelcomeModule()
        suite.test(
            "Welcome module loads",
            welcome.name == "welcome"
        )
        suite.test(
            "Welcome has commands",
            len(welcome.commands) > 0
        )
    except Exception as e:
        suite.test("Welcome module loads", False, str(e))

    # Test locks module
    try:
        from bot.modules.locks import LocksModule
        locks = LocksModule()
        suite.test(
            "Locks module loads",
            locks.name == "locks"
        )
        suite.test(
            "Locks has commands",
            len(locks.commands) > 0
        )
    except Exception as e:
        suite.test("Locks module loads", False, str(e))

    # Test antispam module
    try:
        from bot.modules.antispam import AntispamModule
        antispam = AntispamModule()
        suite.test(
            "Antispam module loads",
            antispam.name == "antispam"
        )
        suite.test(
            "Antispam has commands",
            len(antispam.commands) > 0
        )
    except Exception as e:
        suite.test("Antispam module loads", False, str(e))

    # Test notes module
    try:
        from bot.modules.notes import NotesModule
        notes = NotesModule()
        suite.test(
            "Notes module loads",
            notes.name == "notes"
        )
        suite.test(
            "Notes has commands",
            len(notes.commands) > 0
        )
    except Exception as e:
        suite.test("Notes module loads", False, str(e))

    # Test filters module
    try:
        from bot.modules.filters import FiltersModule
        filters = FiltersModule()
        suite.test(
            "Filters module loads",
            filters.name == "filters"
        )
        suite.test(
            "Filters has commands",
            len(filters.commands) > 0
        )
    except Exception as e:
        suite.test("Filters module loads", False, str(e))

    # Test games module
    try:
        from bot.modules.games import GamesModule
        games = GamesModule()
        suite.test(
            "Games module loads",
            games.name == "games"
        )
        suite.test(
            "Games has commands",
            len(games.commands) > 0
        )
    except Exception as e:
        suite.test("Games module loads", False, str(e))

    suite.print_results()
    return suite.failed == 0


def main():
    """Run all tests."""
    print("="*60)
    print("NEXUS BOT COMPREHENSIVE TEST SUITE")
    print("="*60)

    results = []

    # Run all module tests
    results.append(("Moderation", test_moderation_module()))
    results.append(("Economy", test_economy_module()))
    results.append(("Reputation", test_reputation_module()))
    results.append(("Scheduler", test_scheduler_module()))
    results.append(("Other Modules", test_other_modules()))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for module_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {module_name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
