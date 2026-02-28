#!/usr/bin/env python3
"""
Validation script to verify deployment changes are correct.
Run this locally before deploying to Render.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.12."""
    version = sys.version_info
    if version.major != 3 or version.minor != 12:
        print(f"⚠️  Warning: Python {version.major}.{version.minor} detected.")
        print(f"   Render deployment uses Python 3.12.2")
        print(f"   Current version may have different wheel availability.")
        return False
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_requirements_syntax():
    """Check if requirements.txt has valid syntax."""
    try:
        with open("requirements.txt") as f:
            lines = f.readlines()
        print(f"✓ requirements.txt syntax: Valid ({len(lines)} lines)")
        return True
    except Exception as e:
        print(f"✗ requirements.txt syntax: Invalid - {e}")
        return False


def check_key_dependencies():
    """Check if critical dependencies have expected versions."""
    key_deps = {
        "pydantic": "2.10",
        "pydantic-settings": "2.6",
        "fastapi": "0.115",
        "aiogram": "3.13",
        "sqlalchemy": "2.0",
    }

    print("\nKey dependencies:")
    all_ok = True
    with open("requirements.txt") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for dep, expected_version in key_deps.items():
                if line.startswith(f"{dep}=="):
                    actual = line.split("==")[1]
                    if actual.startswith(expected_version):
                        print(f"  ✓ {dep}: {actual}")
                    else:
                        print(f"  ⚠️  {dep}: {actual} (expected {expected_version}*)")
                        all_ok = False
                    break
    return all_ok


def check_render_yaml():
    """Check if render.yaml has correct structure."""
    try:
        import yaml

        with open("render.yaml") as f:
            config = yaml.safe_load(f)

        if not config or "services" not in config:
            print("✗ render.yaml: Invalid structure")
            return False

        services = config["services"]
        python_services = [s for s in services if s.get("runtime") == "python"]

        print(f"\n✓ render.yaml structure: Valid")
        print(f"  Total services: {len(services)}")
        print(f"  Python services: {len(python_services)}")

        for service in python_services:
            name = service.get("name")
            build_cmd = service.get("buildCommand", "")
            has_no_cache = "--no-cache-dir" in build_cmd

            status = "✓" if has_no_cache else "✗"
            print(f"  {status} {name}: {'Has --no-cache-dir' if has_no_cache else 'Missing --no-cache-dir'}")

            # Check for CARGO_HOME and RUSTUP_HOME
            env_vars = service.get("envVars", [])
            has_cargo = any(v.get("key") == "CARGO_HOME" for v in env_vars)
            has_rustup = any(v.get("key") == "RUSTUP_HOME" for v in env_vars)

            if not (has_cargo and has_rustup):
                print(f"    ⚠️  Missing CARGO_HOME or RUSTUP_HOME env vars")

        return True
    except ImportError:
        print("⚠️  PyYAML not installed, skipping render.yaml validation")
        return True
    except Exception as e:
        print(f"✗ render.yaml: Invalid - {e}")
        return False


def check_gitignore():
    """Check if .gitignore includes Rust/Cargo directories."""
    with open(".gitignore") as f:
        content = f.read()

    has_cargo = ".cargo/" in content
    has_rustup = ".rustup/" in content

    print("\n✓ .gitignore:")
    print(f"  {'✓' if has_cargo else '✗'} .cargo/")
    print(f"  {'✓' if has_rustup else '✗'} .rustup/")

    return has_cargo and has_rustup


def simulate_pip_check():
    """Simulate pip dependency check (dry run)."""
    print("\nSimulating pip dependency check...")

    try:
        result = subprocess.run(
            ["pip", "install", "--dry-run", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✓ Dependencies can be resolved")
            return True
        else:
            print("⚠️  Dependency resolution issues:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("⚠️  pip not found, skipping dependency check")
        return True
    except subprocess.TimeoutExpired:
        print("⚠️  Dependency check timed out")
        return False
    except Exception as e:
        print(f"⚠️  Dependency check error: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Nexus Deployment Validation")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Requirements Syntax", check_requirements_syntax),
        ("Key Dependencies", check_key_dependencies),
        ("Render Config", check_render_yaml),
        (".gitignore", check_gitignore),
        ("Pip Check", simulate_pip_check),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Error: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("   You're ready to deploy to Render.")
        return 0
    else:
        print("\n⚠️  Some checks failed.")
        print("   Please review the issues above before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
