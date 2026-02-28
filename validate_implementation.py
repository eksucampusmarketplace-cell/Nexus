"""
Nexus Bot - Validation Script
Checks that all modules and files are properly structured without importing them.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - FILE NOT FOUND")
        return False


def check_file_content(filepath, required_content, description):
    """Check if file contains required content."""
    if not os.path.exists(filepath):
        print(f"❌ {description} - FILE NOT FOUND")
        return False

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if required_content in content:
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - REQUIRED CONTENT NOT FOUND")
        return False


def main():
    """Run validation checks."""
    print("="*60)
    print("NEXUS BOT VALIDATION")
    print("="*60)

    results = []

    # Check module structure
    print("\n📦 Checking Module Structure...")

    modules_dir = "/home/engine/project/bot/modules"
    if os.path.exists(modules_dir):
        modules = os.listdir(modules_dir)
        print(f"✅ Found {len(modules)} module directories")

        # Check for required __init__.py files
        for module in modules:
            module_path = os.path.join(modules_dir, module)
            init_path = os.path.join(module_path, "__init__.py")
            if os.path.isdir(module_path):
                if os.path.exists(init_path):
                    print(f"  ✅ {module}/__init__.py")
                else:
                    print(f"  ❌ {module}/__init__.py - MISSING")
    else:
        print("❌ Modules directory not found")
        results.append(False)

    # Check specific modules
    print("\n🛡️ Checking Moderation Module...")
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/moderation/__init__.py",
        "Moderation __init__.py"
    ))
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/moderation/module.py",
        "Moderation module.py"
    ))
    results.append(check_file_content(
        "/home/engine/project/bot/modules/moderation/module.py",
        "class ModerationModule",
        "ModerationModule class"
    ))

    print("\n💰 Checking Economy Module...")
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/economy/__init__.py",
        "Economy __init__.py"
    ))
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/economy/module.py",
        "Economy module.py"
    ))
    results.append(check_file_content(
        "/home/engine/project/bot/modules/economy/module.py",
        "class EconomyModule",
        "EconomyModule class"
    ))

    print("\n📊 Checking Reputation Module...")
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/reputation/__init__.py",
        "Reputation __init__.py"
    ))
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/reputation/module.py",
        "Reputation module.py"
    ))
    results.append(check_file_content(
        "/home/engine/project/bot/modules/reputation/module.py",
        "class ReputationModule",
        "ReputationModule class"
    ))

    print("\n📅 Checking Scheduler Module...")
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/scheduler/__init__.py",
        "Scheduler __init__.py"
    ))
    results.append(check_file_exists(
        "/home/engine/project/bot/modules/scheduler/module.py",
        "Scheduler module.py"
    ))
    results.append(check_file_content(
        "/home/engine/project/bot/modules/scheduler/module.py",
        "class SchedulerModule",
        "SchedulerModule class"
    ))

    # Check other modules
    print("\n📦 Checking Other Modules...")

    other_modules = [
        "welcome", "captcha", "antispam", "locks", "notes",
        "filters", "rules", "games", "analytics", "ai_assistant",
        "info", "polls", "cleaning", "formatting", "echo", "help"
    ]

    for module in other_modules:
        init_path = f"/home/engine/project/bot/modules/{module}/__init__.py"
        module_path = f"/home/engine/project/bot/modules/{module}/module.py"
        results.append(check_file_exists(init_path, f"{module} __init__.py"))
        results.append(check_file_exists(module_path, f"{module} module.py"))

    # Check documentation
    print("\n📚 Checking Documentation...")

    docs = [
        ("/home/engine/project/docs/COMPLETE_COMMANDS_REFERENCE.md", "Commands Reference"),
        ("/home/engine/project/docs/COMPLETE_IMPLEMENTATION_SUMMARY.md", "Implementation Summary"),
        ("/home/engine/project/docs/IMPLEMENTATION_COMPLETE.md", "Implementation Complete"),
    ]

    for filepath, description in docs:
        results.append(check_file_exists(filepath, description))

    # Check configuration files
    print("\n⚙️ Checking Configuration Files...")

    configs = [
        ("/home/engine/project/requirements.txt", "requirements.txt"),
        ("/home/engine/project/docker-compose.yml", "docker-compose.yml"),
        ("/home/engine/project/render.yaml", "render.yaml"),
        ("/home/engine/project/.env.example", ".env.example"),
    ]

    for filepath, description in configs:
        results.append(check_file_exists(filepath, description))

    # Check Mini App
    print("\n📱 Checking Mini App...")

    mini_app_files = [
        ("/home/engine/project/mini-app/package.json", "package.json"),
        ("/home/engine/project/mini-app/src/App.tsx", "App.tsx"),
        ("/home/engine/project/mini-app/src/api/index.ts", "API client"),
    ]

    for filepath, description in mini_app_files:
        results.append(check_file_exists(filepath, description))

    # Check API
    print("\n🔌 Checking API...")

    api_files = [
        ("/home/engine/project/api/main.py", "main.py"),
    ]

    for filepath, description in api_files:
        results.append(check_file_exists(filepath, description))

    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"VALIDATION RESULTS: {passed}/{total} checks passed")
    print("="*60)

    if passed == total:
        print("🎉 ALL CHECKS PASSED!")
        return 0
    else:
        print(f"⚠️ {total - passed} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
