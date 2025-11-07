#!/usr/bin/env python3
"""
Pre-flight validation script for PR review system

Run this before testing manually to catch common issues:
- Python syntax errors
- Git repository state problems
- Missing dependencies

Usage:
    python3 validate.py
    python3 validate.py --verbose
"""

import sys
import subprocess
from pathlib import Path
import py_compile
import tempfile


def check_python_syntax(verbose=False):
    """Check Python syntax for all Python files"""
    print("🔍 Checking Python syntax...")

    script_dir = Path(__file__).parent
    python_files = [
        "pr_workflow.py",
        "intelligent_squash.py",
        "conflict_analyzer.py",
        "enhanced_report_generator.py",
        "ai_conversation_analyzer.py",
        "ai_risk_assessor.py",
        "solution_assessor.py",
        "backport_assessor.py",
        "commit_message_generator.py",
        "pr_context_collector.py",
        "claude_code_wrapper.py",
        "batch_pr_workflow.py",
    ]

    errors = []
    for py_file in python_files:
        file_path = script_dir / py_file
        if not file_path.exists():
            if verbose:
                print(f"  ⚠️  {py_file} not found (skipping)")
            continue

        try:
            # Create a temporary compiled file
            with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
                py_compile.compile(str(file_path), cfile=tmp.name, doraise=True)
            if verbose:
                print(f"  ✅ {py_file}")
        except py_compile.PyCompileError as e:
            errors.append(f"{py_file}: {e}")
            print(f"  ❌ {py_file}: {e}")

    if errors:
        print(f"\n❌ Found {len(errors)} syntax error(s)")
        return False
    else:
        print("✅ All Python files have valid syntax\n")
        return True


def check_git_state(verbose=False):
    """Check git repository state"""
    print("🔍 Checking git repository state...")

    script_dir = Path(__file__).parent
    spring_ai_dir = script_dir / "spring-ai"

    if not spring_ai_dir.exists():
        print("  ℹ️  spring-ai directory doesn't exist (will be cloned on first run)")
        print("✅ Git state OK (no repository yet)\n")
        return True

    if not (spring_ai_dir / ".git").exists():
        print(f"  ❌ {spring_ai_dir} exists but is not a git repository")
        print("     Suggestion: rm -rf spring-ai")
        return False

    # Check for stuck rebase
    rebase_head = spring_ai_dir / ".git" / "REBASE_HEAD"
    if rebase_head.exists():
        print("  ⚠️  Repository is in rebase state")
        print("     Suggestion: cd spring-ai && git rebase --abort")
        if verbose:
            print("     (Pre-flight checks will auto-fix this)")
        return True  # Not a blocker - pre-flight will fix

    # Check for unmerged files
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=spring_ai_dir,
            capture_output=True,
            text=True,
            check=True
        )

        unmerged = [line for line in result.stdout.split('\n')
                   if line.startswith(('UU ', 'AA ', 'DD '))]

        if unmerged:
            print(f"  ⚠️  Found {len(unmerged)} unmerged file(s)")
            if verbose:
                for line in unmerged[:5]:  # Show first 5
                    print(f"     {line}")
            print("     Suggestion: cd spring-ai && git reset --hard HEAD")
            return True  # Not a blocker - pre-flight will fix

        if verbose:
            print("  ✅ No rebase state detected")
            print("  ✅ No unmerged files")

        print("✅ Git state OK\n")
        return True

    except subprocess.CalledProcessError as e:
        print(f"  ❌ Could not check git status: {e}")
        return False


def check_dependencies(verbose=False):
    """Check for required dependencies"""
    print("🔍 Checking dependencies...")

    missing = []

    # Check gh CLI
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        if verbose:
            version = result.stdout.split('\n')[0]
            print(f"  ✅ GitHub CLI: {version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("gh (GitHub CLI)")
        print("  ❌ GitHub CLI (gh) not found")

    # Check git
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        if verbose:
            print(f"  ✅ {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("git")
        print("  ❌ git not found")

    # Check Python version
    if sys.version_info < (3, 8):
        missing.append("Python 3.8+")
        print(f"  ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.8+)")
    elif verbose:
        print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor}")

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        return False
    else:
        print("✅ All dependencies available\n")
        return True


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("🚀 PR Review System Validation\n")
    print("=" * 50)
    print()

    results = []

    # Run all checks
    results.append(("Python Syntax", check_python_syntax(verbose)))
    results.append(("Git State", check_git_state(verbose)))
    results.append(("Dependencies", check_dependencies(verbose)))

    # Summary
    print("=" * 50)
    print("\n📊 Validation Summary:")

    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check_name}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("✅ All checks passed! Safe to run PR workflow.")
        return 0
    else:
        print("❌ Some checks failed. Please fix issues before running.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
