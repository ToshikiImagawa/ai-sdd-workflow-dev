#!/usr/bin/env python3
"""
validate-files.py
Scan specification and requirement files for /constitution validate
Reduces Claude's Glob/Grep overhead by pre-scanning file structure
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def log(message: str) -> None:
    """Print log message to stderr"""
    print(f"[validate-files] {message}", file=sys.stderr)


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
    """Read .sdd-config.json (paths only)"""
    config_file = project_root / ".sdd-config.json"
    if not config_file.exists():
        print("ERROR: .sdd-config.json not found", file=sys.stderr)
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    directories = config.get("directories", {})
    return {
        "root": config.get("root", ".sdd"),
        "requirement": directories.get("requirement", "requirement"),
        "specification": directories.get("specification", "specification"),
    }


def sorted_matches(base: Path, pattern: str) -> list:
    """Return regular files under base matching pattern, sorted by path string"""
    matches = [str(p) for p in base.rglob(pattern) if p.is_file()]
    matches.sort()
    return matches


def write_lines(path: Path, lines: list) -> None:
    """Write lines to a file, one per line (mirrors `... > file`)"""
    content = "".join(f"{line}\n" for line in lines)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    """Main execution"""
    try:
        project_root = get_project_root()
        config = read_config(project_root)

        requirement_path = (
            project_root / config["root"] / config["requirement"]
        )
        specification_path = (
            project_root / config["root"] / config["specification"]
        )

        output_dir = project_root / config["root"] / ".cache" / "constitution"
        output_dir.mkdir(parents=True, exist_ok=True)

        requirement_files = output_dir / "requirement_files.txt"
        spec_files = output_dir / "spec_files.txt"
        design_files = output_dir / "design_files.txt"
        summary_file = output_dir / "scan_summary.json"

        # --- Phase 1: Scan requirement files ---
        log("Scanning requirement files...")
        requirement_count = 0
        if requirement_path.is_dir():
            matches = sorted_matches(requirement_path, "*.md")
            write_lines(requirement_files, matches)
            requirement_count = len(matches)
            log(f"Found {requirement_count} requirement files")
        else:
            log(f"Requirement directory not found: {requirement_path}")

        # --- Phase 2: Scan specification files ---
        log("Scanning specification files...")
        spec_count = 0
        design_count = 0
        if specification_path.is_dir():
            spec_matches = sorted_matches(specification_path, "*_spec.md")
            design_matches = sorted_matches(specification_path, "*_design.md")
            write_lines(spec_files, spec_matches)
            write_lines(design_files, design_matches)
            spec_count = len(spec_matches)
            design_count = len(design_matches)
            log(f"Found {spec_count} specification files")
            log(f"Found {design_count} design files")
        else:
            log(f"Specification directory not found: {specification_path}")

        # --- Phase 3: Generate summary ---
        summary = {
            "scanned_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "requirement_files": requirement_count,
            "spec_files": spec_count,
            "design_files": design_count,
            "total_files": requirement_count + spec_count + design_count,
        }
        summary_file.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        log(f"Summary: {summary_file.read_text(encoding='utf-8').strip()}")

        # --- Phase 4: Export to CLAUDE_ENV_FILE ---
        env_file = os.environ.get("CLAUDE_ENV_FILE")
        if env_file:
            env_file_path = Path(env_file)

            # Remove existing CONSTITUTION_* variables
            if env_file_path.exists():
                lines = [
                    line
                    for line in env_file_path.read_text(
                        encoding="utf-8"
                    ).splitlines(keepends=True)
                    if not line.startswith("export CONSTITUTION_")
                ]
                env_file_path.write_text("".join(lines), encoding="utf-8")

            with open(env_file_path, "a", encoding="utf-8") as f:
                f.write(f'export CONSTITUTION_CACHE_DIR="{output_dir}"\n')
                f.write(
                    f'export CONSTITUTION_REQUIREMENT_FILES="{requirement_files}"\n'
                )
                f.write(f'export CONSTITUTION_SPEC_FILES="{spec_files}"\n')
                f.write(f'export CONSTITUTION_DESIGN_FILES="{design_files}"\n')
                f.write(f'export CONSTITUTION_SUMMARY="{summary_file}"\n')

            log("Environment variables exported to CLAUDE_ENV_FILE")

        log("Scan complete")
        log(f"Cache location: {output_dir}")

    except SystemExit:
        raise
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
