#!/usr/bin/env python3
"""
find-spec-docs.py
Find specification documents and related files for /check-spec
Reduces Claude's Glob/Grep overhead by pre-scanning file structure

The comparison baseline is the abstract specification under specification/
(the ``_spec`` suffix is optional). Technical design documents live at
``task/{ticket-number}/design-draft.md`` and are deleted after implementation,
so they are collected as an *optional* auxiliary input: their absence is the
normal state, never a warning.
"""

import json
import sys
from pathlib import Path

# Shared modules live in plugins/sdd-workflow/scripts (three levels up + scripts).
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from doc_walker import iter_all_markdown, iter_specification_docs  # noqa: E402
from env_export import rewrite_exports  # noqa: E402
from hook_common import SddPaths, load_sdd_paths, resolve_project_root  # noqa: E402
from naming import DESIGN_SUFFIX, SPEC_SUFFIX, feature_name, is_design_stem  # noqa: E402

# Design drafts are ticket-scoped with a fixed filename, so they cannot be
# matched to a spec by stem.
DESIGN_DRAFT_NAME = "design-draft.md"


def log(message: str) -> None:
    """Print log message to stderr"""
    print(f"[find-spec-docs] {message}", file=sys.stderr)


def read_config(project_root: Path) -> SddPaths:
    """Resolve the .sdd layout, requiring an initialized project"""
    config_file = project_root / ".sdd-config.json"
    if not config_file.exists():
        print("ERROR: .sdd-config.json not found", file=sys.stderr)
        sys.exit(1)
    return load_sdd_paths(str(project_root))


def sorted_docs(paths) -> list:
    """Sorted unique file paths, excluding v4.x persisted design docs.

    A ``{feature}_design.md`` under specification/ is a design doc, not a spec
    (see naming.is_design_stem), so it never enters the spec list; it is exposed
    as the optional ``design`` field of a mapping entry instead.
    """
    return sorted({
        str(p) for p in paths if p.is_file() and not is_design_stem(p.stem)
    })


def write_lines(path: Path, lines: list) -> None:
    """Write lines to a file, one per line (mirrors `... > file`)"""
    content = "".join(f"{line}\n" for line in lines)
    path.write_text(content, encoding="utf-8")


def find_spec_documents(specification_path: Path, target: str) -> list:
    """Locate the spec documents to check, as sorted path strings.

    Both naming forms are matched because the ``_spec`` suffix is optional under
    specification/: ``{feature}_spec.md`` and ``{feature}.md``.
    """
    log("Scanning specification documents...")

    if not specification_path.is_dir():
        log(f"ERROR: Specification directory not found: {specification_path}")
        sys.exit(1)

    if not target:
        log("Searching for all specification documents...")
        specs = sorted_docs(iter_specification_docs(specification_path))
        log(f"Found {len(specs)} specification documents")
        return specs

    log(f"Searching for feature: {target}")

    # Exact matches first: flat (both suffix forms), then a feature directory
    # (hierarchical structure, e.g. auth/index.md + auth/user-login_spec.md).
    specs = sorted_docs([
        specification_path / f"{target}{SPEC_SUFFIX}.md",
        specification_path / f"{target}.md",
        *iter_all_markdown(specification_path / target),
    ])
    if specs:
        log(f"Found {len(specs)} specification file(s) for: {target}")
        return specs

    # Fall back to partial matches
    specs = sorted_docs(specification_path.rglob(f"*{target}*.md"))
    if specs:
        log(f"Found {len(specs)} matching specification file(s)")
    else:
        log(f"WARNING: No specification document found for: {target}")
    return specs


def find_design_drafts(task_path: Path) -> list:
    """Locate design drafts (``task/{ticket-number}/design-draft.md``).

    Optional auxiliary input: an empty result is the normal state once
    implementation completes, so it is logged without a warning.
    """
    if not task_path.is_dir():
        log("No task directory; skipping design draft scan")
        return []

    drafts = sorted_docs(task_path.rglob(DESIGN_DRAFT_NAME))
    log(f"Found {len(drafts)} design draft(s) (optional auxiliary input)")
    return drafts


def generate_mapping(specs: list, drafts: list, mapping_file: Path) -> None:
    """Build spec -> feature -> auxiliary design mapping JSON"""
    documents = []

    for spec_file in specs:
        spec_path = Path(spec_file)
        basename = feature_name(spec_path.stem)

        # v4.x projects may still keep a sibling persisted design doc.
        design_candidate = spec_path.parent / f"{basename}{DESIGN_SUFFIX}.md"
        design_file = str(design_candidate) if design_candidate.is_file() else ""

        documents.append(
            {
                "spec": spec_file,
                "feature_name": basename,
                "design": design_file,
            }
        )

    mapping = {"spec_documents": documents, "design_drafts": drafts}
    mapping_file.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log("File mapping generated")


def export_env_vars(
    output_dir: Path,
    spec_files: Path,
    design_draft_files: Path,
    mapping_file: Path,
) -> None:
    """Export metadata to CLAUDE_ENV_FILE"""
    wrote = rewrite_exports("CHECK_SPEC_", [
        f'export CHECK_SPEC_CACHE_DIR="{output_dir}"',
        f'export CHECK_SPEC_SPEC_FILES="{spec_files}"',
        f'export CHECK_SPEC_DESIGN_DRAFT_FILES="{design_draft_files}"',
        f'export CHECK_SPEC_MAPPING="{mapping_file}"',
    ])
    if wrote:
        log("Environment variables exported to CLAUDE_ENV_FILE")


def main() -> None:
    """Main execution"""
    try:
        project_root = Path(resolve_project_root())
        paths = read_config(project_root)

        sdd_dir = project_root / paths.root

        # Target feature name (optional argument)
        target = sys.argv[1] if len(sys.argv) > 1 else ""

        output_dir = sdd_dir / ".cache" / "check-spec"
        output_dir.mkdir(parents=True, exist_ok=True)

        spec_files = output_dir / "spec_files.txt"
        design_draft_files = output_dir / "design_draft_files.txt"
        mapping_file = output_dir / "file_mapping.json"

        specs = find_spec_documents(
            sdd_dir / paths.specification_dir, target
        )
        drafts = find_design_drafts(sdd_dir / paths.task_dir)

        write_lines(spec_files, specs)
        write_lines(design_draft_files, drafts)
        generate_mapping(specs, drafts, mapping_file)
        export_env_vars(
            output_dir, spec_files, design_draft_files, mapping_file
        )

        log("Scan complete")
        log(f"Cache location: {output_dir}")

    except SystemExit:
        raise
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
