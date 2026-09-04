#!/usr/bin/env python3
"""
run-verification.py
Detect the project's toolchain and run one verification category
(test / lint / typecheck / security) for the /run-checklist skill.

This script exists so the skill's `allowed-tools` can pre-approve a single
scoped Bash invocation (per this repo's Check 5.4 convention) instead of a
bare `Bash` grant. The category-to-command mapping mirrors
`references/verification_commands.md`; see that file for the full mapping
this script implements. Claude reads the JSON result on stdout — the script
owns command detection and execution, Claude only interprets the outcome.
"""

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional

VALID_CATEGORIES = ("test", "lint", "typecheck", "security")

# (detection file, project type), checked in this order (see verification_commands.md
# "Detection Priority").
DETECTION_ORDER = (
    ("package.json", "node"),
    ("pyproject.toml", "python"),
    ("Cargo.toml", "rust"),
    ("go.mod", "go"),
    ("setup.py", "python"),
    ("requirements.txt", "python"),
    ("Gemfile", "ruby"),
)

# Candidate commands per (project_type, category), tried in order until one's
# executable is found. Each command's first token is checked with shutil.which
# semantics (via FileNotFoundError) so an unavailable tool falls through to
# the next candidate, or to SKIPPED if none are available.
COMMANDS = {
    "node": {
        "test": ["npm test"],
        "lint": ["npx eslint .", "eslint ."],
        "typecheck": ["npx tsc --noEmit", "tsc --noEmit"],
        "security": ["npm audit"],
    },
    "python": {
        "test": ["pytest"],
        "lint": ["ruff check ."],
        "typecheck": ["mypy ."],
        "security": ["pip-audit", "safety check"],
    },
    "rust": {
        "test": ["cargo test"],
        "lint": ["cargo clippy"],
        "typecheck": [],  # built into `cargo build`; no separate step
        "security": ["cargo audit"],
    },
    "go": {
        "test": ["go test ./..."],
        "lint": ["golangci-lint run"],
        "typecheck": [],  # built into `go build`; no separate step
        "security": ["govulncheck ./..."],
    },
    "ruby": {
        "test": ["bundle exec rspec"],
        "lint": ["bundle exec rubocop"],
        "typecheck": [],
        "security": ["bundle exec bundler-audit"],
    },
}

TIMEOUT_SECONDS = 300


def log(message: str) -> None:
    print(f"[run-verification] {message}", file=sys.stderr)


def detect_project_type(project_root: Path) -> Optional[str]:
    for filename, project_type in DETECTION_ORDER:
        if (project_root / filename).exists():
            return project_type
    # No manifest file present. Fall back to a directory-shape heuristic so
    # minimal projects (e.g. a `tests/` folder with no packaging metadata
    # yet) still get verified instead of silently skipped.
    if any((project_root / d).glob("test_*.py") or (project_root / d).glob("*_test.py")
           for d in ("tests", "test") if (project_root / d).is_dir()):
        return "python"
    return None


def run_command(command: str, cwd: Path) -> dict:
    args = shlex.split(command)
    try:
        result = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
        return {
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-4000:],
        }
    except FileNotFoundError:
        return {"status": "TOOL_NOT_FOUND", "command": command}
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "command": command,
            "timeout_seconds": TIMEOUT_SECONDS,
        }


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in VALID_CATEGORIES:
        log(f"Usage: run-verification.py <{'|'.join(VALID_CATEGORIES)}>")
        sys.exit(2)
    category = sys.argv[1]

    project_root = Path.cwd()
    project_type = detect_project_type(project_root)

    if project_type is None:
        result = {
            "category": category,
            "project_type": None,
            "status": "SKIPPED",
            "reason": "No recognized project manifest found "
                      "(package.json, pyproject.toml, Cargo.toml, go.mod, setup.py, "
                      "requirements.txt, Gemfile).",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    candidates = COMMANDS.get(project_type, {}).get(category, [])
    if not candidates:
        result = {
            "category": category,
            "project_type": project_type,
            "status": "SKIPPED",
            "reason": f"No {category} command is defined for project type '{project_type}' "
                      "(e.g. this category has no separate tool for this ecosystem).",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    attempts = []
    for command in candidates:
        outcome = run_command(command, project_root)
        attempts.append(outcome)
        if outcome["status"] not in ("TOOL_NOT_FOUND",):
            result = {"category": category, "project_type": project_type, **outcome}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

    result = {
        "category": category,
        "project_type": project_type,
        "status": "SKIPPED",
        "reason": f"None of the candidate tools were installed: {[c for c in candidates]}",
        "attempts": attempts,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
