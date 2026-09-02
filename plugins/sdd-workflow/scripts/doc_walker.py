"""doc_walker.py - Shared AI-SDD document discovery.

Single source of truth for the target-selection rule that was duplicated between
sdd_index.iter_target_files and scan-documents.collect_documents:

- requirement/: every ``.md`` file
- specification/: every ``.md`` file (the ``_spec``/``_design`` suffix is optional
  since specification/ is a single-type directory identified by directory alone;
  see naming.py)
- task/: every ``.md`` file

Also hosts find_spec_doc (used by the post-tool-use hook). All traversal is
pathlib-based for cross-platform behavior.
"""

from pathlib import Path
from typing import List, Union

from naming import SPEC_SUFFIX

PathLike = Union[str, Path]


def iter_requirement_docs(req_path: PathLike) -> List[Path]:
    """Every ``.md`` file under a requirement directory, sorted."""
    p = Path(req_path)
    return sorted(p.rglob("*.md")) if p.is_dir() else []


def iter_specification_docs(spec_path: PathLike) -> List[Path]:
    """Every ``.md`` file under a specification directory, sorted (suffix optional)."""
    p = Path(spec_path)
    return sorted(p.rglob("*.md")) if p.is_dir() else []


def iter_all_markdown(path: PathLike) -> List[Path]:
    """Every ``.md`` file under a directory, sorted."""
    p = Path(path)
    return sorted(p.rglob("*.md")) if p.is_dir() else []


def iter_target_files(project_root: str, sdd_root: str,
                      req_dir: str, spec_dir: str) -> List[str]:
    """Indexer targets: requirement (all) + specification (all), globally sorted."""
    base = Path(project_root) / sdd_root
    files = iter_requirement_docs(base / req_dir) + iter_specification_docs(base / spec_dir)
    return sorted(str(f) for f in files)


def collect_documents(sdd_dir: PathLike, requirement_dir: str,
                      specification_dir: str, task_dir: str) -> List[Path]:
    """Scan targets: requirement (all) + specification (all) + task (all).

    Returned in section order (requirement, then specification, then task), each
    section sorted internally.
    """
    base = Path(sdd_dir)
    docs = iter_requirement_docs(base / requirement_dir)
    docs += iter_specification_docs(base / specification_dir)
    docs += iter_all_markdown(base / task_dir)
    return docs


def find_spec_doc(spec_dir: PathLike, stem: str) -> str:
    """Return the path of the spec document matching ``stem`` under spec_dir, or ''.

    ``{stem}_design.md`` never matches: design docs are no longer persisted under
    specification/, so they are not a valid sync target. When several files share
    a stem the lowest path string wins, so the result is deterministic.
    """
    base = Path(spec_dir)
    # Suffix-first so an explicit {stem}_spec.md wins over a bare {stem}.md.
    for suffix in (f"{SPEC_SUFFIX}.md", ".md"):
        found = min((str(p) for p in base.rglob(f"{stem}{suffix}")), default="")
        if found:
            return found
    return ""
