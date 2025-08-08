#!/usr/bin/env python3

from pathlib import Path

# Test the path construction
script_dir = Path(__file__).parent
repo_dir = script_dir / "start-spring-io"
application_yml = repo_dir / "start-site" / "src" / "main" / "resources" / "application.yml"

print(f"Script dir: {script_dir}")
print(f"Repo dir: {repo_dir}")
print(f"Application YAML: {application_yml}")

print("✅ Path construction test passed")