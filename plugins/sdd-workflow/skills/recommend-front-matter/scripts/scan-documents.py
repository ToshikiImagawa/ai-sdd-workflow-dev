#!/usr/bin/env python3
"""
scan-documents.py
Scan AI-SDD documents for Front Matter presence
Used by /recommend-front-matter skill

Python port of scan-documents.sh (removes find/grep/sed/jq dependencies for
cross-platform support). Behavior, output files, cache location and exported
environment variables are kept identical to the original shell script.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def log(message: str) -> None:
    """Print log message to stderr"""
    print(f"[scan-documents] {message}", file=sys.stderr)


def get_project_root() -> Path:
    """Get project root directory"""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)

    # Try git root
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def read_config(project_root: Path) -> dict:
    """Read .sdd-config.json and resolve paths with defaults"""
    config_file = project_root / ".sdd-config.json"
    if not config_file.exists():
        log("ERROR: .sdd-config.json not found")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    directories = config.get("directories") or {}
    return {
        "root": config.get("root") or ".sdd",
        "requirement": directories.get("requirement") or "requirement",
        "specification": directories.get("specification") or "specification",
        "task": directories.get("task") or "task",
        "lang": config.get("lang") or "en",
    }


def read_lines(file: Path) -> list:
    """Read file as a list of lines (without trailing newlines)"""
    try:
        with open(file, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def has_front_matter(lines: list) -> tuple:
    """Check if the document starts with a Front Matter block.

    Returns (has_fm, closing_index) where closing_index is the 0-based line
    index of the closing '---'. Mirrors the shell logic: the first line must be
    '---' and a closing '---' must appear within the first 50 lines.
    """
    if not lines or lines[0].rstrip("\r") != "---":
        return (False, 0)

    for i in range(1, min(50, len(lines))):
        if lines[i].rstrip("\r") == "---":
            return (True, i)
    return (False, 0)


def determine_type(
    filepath: str,
    basename: str,
    requirement_dir: str,
    specification_dir: str,
    task_dir: str,
) -> str:
    """Determine document type from file path and naming convention"""
    if f"/{requirement_dir}/" in filepath:
        return "prd"
    if f"/{specification_dir}/" in filepath:
        if basename.endswith("_spec"):
            return "spec"
        if basename.endswith("_design"):
            return "design"
        return "unknown"
    if f"/{task_dir}/" in filepath:
        if "implementation_log" in basename or "impl_log" in basename:
            return "implementation-log"
        return "task"
    return "unknown"


def extract_title(lines: list, basename: str) -> str:
    """Extract title from the first '# ' heading, skipping Front Matter.

    Falls back to the basename when no heading is found.
    """
    has_fm, closing_index = has_front_matter(lines)
    start = closing_index + 1 if has_fm else 0

    for line in lines[start:]:
        if re.match(r"^#\s", line):
            title = re.sub(r"^#\s*", "", line)
            if title:
                return title
            break

    return basename


def collect_documents(config: dict, sdd_dir: Path) -> list:
    """Collect target markdown documents from requirement/specification/task."""
    requirement_path = sdd_dir / config["requirement"]
    specification_path = sdd_dir / config["specification"]
    task_path = sdd_dir / config["task"]

    documents = []

    # requirement/: all .md files
    if requirement_path.is_dir():
        documents.extend(sorted(requirement_path.rglob("*.md")))

    # specification/: only *_spec.md and *_design.md
    if specification_path.is_dir():
        for file in sorted(specification_path.rglob("*.md")):
            basename = file.name[:-3]  # strip .md
            if basename.endswith("_spec") or basename.endswith("_design"):
                documents.append(file)

    # task/: all .md files
    if task_path.is_dir():
        documents.extend(sorted(task_path.rglob("*.md")))

    return documents


def export_env_vars(scan_result: Path, output_dir: Path, sdd_lang: str) -> None:
    """Export metadata to CLAUDE_ENV_FILE"""
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return

    env_file_path = Path(env_file)

    # Remove existing RECOMMEND_FM_* variables
    if env_file_path.exists():
        with open(env_file_path, "r", encoding="utf-8") as f:
            lines = [
                line for line in f if not line.startswith("export RECOMMEND_FM_")
            ]
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    # Write environment variables
    with open(env_file_path, "a", encoding="utf-8") as f:
        f.write(f'export RECOMMEND_FM_CACHE_DIR="{output_dir}"\n')
        f.write(f'export RECOMMEND_FM_SCAN_RESULT="{scan_result}"\n')
        f.write(f'export SDD_LANG="{sdd_lang}"\n')

    log("Environment variables exported to CLAUDE_ENV_FILE")


def main() -> None:
    """Main execution"""
    try:
        project_root = get_project_root()
        config = read_config(project_root)

        sdd_dir = project_root / config["root"]
        output_dir = sdd_dir / ".cache" / "recommend-front-matter"
        output_dir.mkdir(parents=True, exist_ok=True)

        # --- Phase 1: Scan documents ---
        log("Scanning AI-SDD documents...")
        documents = collect_documents(config, sdd_dir)
        total_count = len(documents)
        log(f"Found {total_count} total documents")

        # --- Phase 2: Analyze documents and build JSON ---
        with_fm_count = 0
        without_fm_count = 0
        entries = []

        for file in documents:
            lines = read_lines(file)
            basename = file.name[:-3]  # strip .md
            filepath = str(file)

            has_fm, _ = has_front_matter(lines)
            if has_fm:
                with_fm_count += 1
            else:
                without_fm_count += 1

            doc_type = determine_type(
                filepath,
                basename,
                config["requirement"],
                config["specification"],
                config["task"],
            )
            title = extract_title(lines, basename)

            try:
                relative_path = str(file.relative_to(sdd_dir))
            except ValueError:
                relative_path = filepath

            entries.append(
                {
                    "path": filepath,
                    "relative_path": relative_path,
                    "basename": basename,
                    "type": doc_type,
                    "has_front_matter": has_fm,
                    "title_line": title,
                }
            )

        result = {
            "scan_timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "total_documents": total_count,
            "documents_with_front_matter": with_fm_count,
            "documents_without_front_matter": without_fm_count,
            "documents": entries,
        }

        scan_result = output_dir / "scan_result.json"
        with open(scan_result, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")

        log("Scan complete")
        log(
            f"Total: {total_count}, With Front Matter: {with_fm_count}, "
            f"Without: {without_fm_count}"
        )

        # --- Phase 3: Export to CLAUDE_ENV_FILE ---
        export_env_vars(scan_result, output_dir, config["lang"])

        log(f"Results saved to: {scan_result}")

    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
