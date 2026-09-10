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

Design drafts are ticket-scoped. Several tickets may be in flight at once, so a
draft is only attached to the check when it can be tied to the run:
``--ticket <n>`` (or ``--ticket=<n>``) selects one ticket directory; otherwise a
draft's front matter ``depends-on`` is matched against the target specs' IDs.
When neither basis resolves and more than one draft exists, no draft is attached
and the drafts are reported as unscoped so the caller can re-run with
``--ticket``.
"""

import json
import sys
from pathlib import Path

# Shared modules live in plugins/sdd-workflow/scripts (three levels up + scripts).
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from doc_walker import iter_all_markdown, iter_specification_docs  # noqa: E402
from env_export import rewrite_exports  # noqa: E402
from fm_parser import parse_front_matter, split_front_matter  # noqa: E402
from hook_common import SddPaths, load_sdd_paths, resolve_project_root  # noqa: E402
from naming import DESIGN_SUFFIX, SPEC_SUFFIX, feature_name, is_design_stem  # noqa: E402

# Design drafts are ticket-scoped with a fixed filename, so they cannot be
# matched to a spec by stem.
DESIGN_DRAFT_NAME = "design-draft.md"
TICKET_FLAG = "--ticket"
SPEC_ID_PREFIX = "spec-"


def log(message: str) -> None:
    """Print log message to stderr"""
    print(f"[find-spec-docs] {message}", file=sys.stderr)


def read_config(project_root: Path) -> SddPaths:
    """Resolve the .sdd layout: .sdd-config.json if present, else defaults"""
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


def read_front_matter(path: Path) -> dict:
    """Parse a document's front matter, tolerating unreadable files."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    fm_text, _ = split_front_matter(text)
    if not fm_text:
        return {}
    return parse_front_matter(fm_text)


def spec_identifiers(specs: list, specification_path: Path) -> set:
    """Collect the IDs a design draft may reference for the target specs.

    Both the declared front matter ``id`` and the ID derived from the file's
    location (``spec-{feature}`` / ``spec-{parent}-{feature}``) are collected,
    so specs that predate front matter can still be matched.
    """
    identifiers = set()
    for spec_file in specs:
        spec_path = Path(spec_file)
        declared = read_front_matter(spec_path).get("id", "")
        if declared:
            identifiers.add(declared)

        basename = feature_name(spec_path.stem)
        identifiers.add(f"{SPEC_ID_PREFIX}{basename}")
        try:
            parent = spec_path.parent.relative_to(specification_path).parts
        except ValueError:
            parent = ()
        if parent:
            identifiers.add(
                SPEC_ID_PREFIX + "-".join([*parent, basename])
            )
    return identifiers


def find_design_drafts(task_path: Path) -> list:
    """Locate every design draft (``task/{ticket-number}/design-draft.md``).

    Optional auxiliary input: an empty result is the normal state once
    implementation completes, so it is logged without a warning. Which of these
    drafts actually belongs to the current check is decided by
    :func:`select_design_drafts`.
    """
    if not task_path.is_dir():
        log("No task directory; skipping design draft scan")
        return []

    drafts = sorted_docs(task_path.rglob(DESIGN_DRAFT_NAME))
    log(f"Found {len(drafts)} design draft(s) (optional auxiliary input)")
    return drafts


def select_design_drafts(
    drafts: list,
    ticket: str = "",
    spec_ids=frozenset(),
) -> tuple:
    """Narrow the design drafts down to the ones that belong to this check.

    Returns ``(selected, unscoped, scope)``:

    - ``selected`` — drafts to use as auxiliary input. An empty result is the
      normal state once implementation completes, so it is not a defect.
    - ``unscoped`` — drafts found but deliberately **not** attached because they
      could not be tied to this run (``scope == "unscoped"``).
    - ``scope`` — how the selection was made: ``none`` (no draft exists),
      ``ticket``, ``depends-on``, ``sole-draft``, or ``unscoped``.

    Attaching every draft in ``task/`` would mix another ticket's design into the
    check, so a draft is only used when the ticket argument or its front matter
    ``depends-on`` ties it to the target specs. A single draft is the one
    exception: with only one ticket in flight there is nothing to mix in.
    """
    if not drafts:
        return [], [], "none"

    if ticket:
        scoped = [d for d in drafts if Path(d).parent.name == ticket]
        if scoped:
            log(f"Using {len(scoped)} design draft(s) for ticket: {ticket}")
        else:
            log(f"No design draft found for ticket: {ticket}")
        return scoped, [], "ticket"

    if spec_ids:
        linked = [
            d for d in drafts
            if set(read_front_matter(Path(d)).get("depends-on", []) or [])
            & set(spec_ids)
        ]
        if linked:
            log(
                f"Using {len(linked)} design draft(s) linked to the target "
                "spec(s) via depends-on"
            )
            return linked, [], "depends-on"

    if len(drafts) == 1:
        log("Using the single design draft found (only ticket in flight)")
        return drafts, [], "sole-draft"

    log(
        f"WARNING: {len(drafts)} design drafts found but none could be tied to "
        f"this check; none will be used. Re-run with {TICKET_FLAG} <number> to "
        "pick one, or add depends-on to the drafts' front matter"
    )
    return [], drafts, "unscoped"


def generate_mapping(
    specs: list,
    drafts: list,
    unscoped_drafts: list,
    scope: str,
    mapping_file: Path,
) -> None:
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

    mapping = {
        "spec_documents": documents,
        "design_drafts": drafts,
        "design_draft_scope": scope,
        "unscoped_design_drafts": unscoped_drafts,
    }
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
    scope: str,
) -> None:
    """Export metadata to CLAUDE_ENV_FILE"""
    wrote = rewrite_exports("CHECK_SPEC_", [
        f'export CHECK_SPEC_CACHE_DIR="{output_dir}"',
        f'export CHECK_SPEC_SPEC_FILES="{spec_files}"',
        f'export CHECK_SPEC_DESIGN_DRAFT_FILES="{design_draft_files}"',
        f'export CHECK_SPEC_DESIGN_DRAFT_SCOPE="{scope}"',
        f'export CHECK_SPEC_MAPPING="{mapping_file}"',
    ])
    if wrote:
        log("Environment variables exported to CLAUDE_ENV_FILE")


def parse_args(argv: list) -> tuple:
    """Parse the CLI arguments into ``(target, ticket)``.

    Accepts both ``--ticket <number>`` and ``--ticket=<number>``. The first
    non-flag argument is the target feature name; any other flag (e.g.
    ``--full``, which the skill handles itself) is ignored so that it is never
    mistaken for a feature name.
    """
    target = ""
    ticket = ""
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == TICKET_FLAG:
            if i + 1 < len(argv):
                ticket = argv[i + 1]
                i += 1
            else:
                log(f"WARNING: {TICKET_FLAG} given without a number; ignoring")
        elif arg.startswith(f"{TICKET_FLAG}="):
            ticket = arg.split("=", 1)[1]
        elif arg.startswith("-"):
            pass
        elif not target:
            target = arg
        i += 1
    return target, ticket


def main() -> None:
    """Main execution"""
    try:
        project_root = Path(resolve_project_root())
        paths = read_config(project_root)

        sdd_dir = project_root / paths.root

        # Target feature name and ticket number (both optional)
        target, ticket = parse_args(sys.argv[1:])

        output_dir = sdd_dir / ".cache" / "check-spec"
        output_dir.mkdir(parents=True, exist_ok=True)

        spec_files = output_dir / "spec_files.txt"
        design_draft_files = output_dir / "design_draft_files.txt"
        mapping_file = output_dir / "file_mapping.json"

        specification_path = sdd_dir / paths.specification_dir
        specs = find_spec_documents(specification_path, target)

        all_drafts = find_design_drafts(sdd_dir / paths.task_dir)
        # Spec IDs are only needed to link drafts, so resolve them lazily.
        spec_ids = (
            spec_identifiers(specs, specification_path)
            if all_drafts and not ticket
            else frozenset()
        )
        drafts, unscoped_drafts, scope = select_design_drafts(
            all_drafts, ticket, spec_ids
        )

        write_lines(spec_files, specs)
        write_lines(design_draft_files, drafts)
        generate_mapping(
            specs, drafts, unscoped_drafts, scope, mapping_file
        )
        export_env_vars(
            output_dir, spec_files, design_draft_files, mapping_file, scope
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
