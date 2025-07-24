#!/usr/bin/env bash

# Simple wrapper script to maintain shell interface while using Python implementation
# This replaces the problematic shell scripts with robust Python code

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the Python workflow with all arguments passed through
exec python3 "$SCRIPT_DIR/pr_workflow.py" "$@"