"""laws_header.py - Shared parsing of Bend law-file conventions (proof gate).

Single source of truth for the leading-comment conventions (``# spec:`` /
``# approved:`` / ``# model-of:``), the law-body content hash that binds an
approval to the law text, the import allowlist, and the ``law`` declaration
check. Consumed by run-verification.py (proof category) and post-tool-use.py.

The conventions themselves are defined in proof-gate_spec.md (FR-004 / FR-005)
and design-draft §5.4; keep this module the only place that encodes them.
"""

import datetime
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional

LAWS_FILE = "LAWS.bend"
PROOF_FILE = "PROOF.bend"
MODEL_FILE = "main.bend"

HEADER_RE = re.compile(r"^#\s*([A-Za-z][\w-]*):\s*(.*)$")
APPROVED_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<approver>\S+)\s+sha256:(?P<digest>[0-9a-f]{12})$"
)
IMPORT_LINE_RE = re.compile(r"^\s*(?:import|from)\b")
# Whole-line match: a trailing comment, an alias or a `from` form never matches
# and therefore fails the allowlist.
LOCAL_IMPORT_RE = re.compile(
    r"^import\s+(?P<target>(?:\./)?(?:[A-Za-z0-9_\-]+/)*[A-Za-z0-9_\-]+(?:\.bend)?)$"
)
LAWS_IMPORT_RE = re.compile(r"^import\s+(?:\./)?LAWS(?:\.bend)?$")
# Bend's bundled standard library: importable by bare name without a file in
# the laws directory.
STDLIB_IMPORTS = frozenset({"Base"})
LAW_DECL_RE = re.compile(r"^\s*law\s+[A-Za-z_]")


def _read_lines(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("﻿"):
        text = text[1:]
    return text.splitlines()


def _header_end(lines: List[str]) -> int:
    """Index of the first line that is neither blank nor a ``#`` comment."""
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        i += 1
    return i


def read_header(path: Path) -> Dict[str, List[str]]:
    """Parse leading ``# key: value`` comment lines; stop at the first code line.

    Every key is collected as a list (``model-of`` is legitimately repeated);
    callers read the keys they know (``spec`` / ``approved`` / ``model-of``)
    and ignore the rest.
    """
    header: Dict[str, List[str]] = {}
    lines = _read_lines(path)
    for raw in lines[:_header_end(lines)]:
        m = HEADER_RE.match(raw.strip())
        if m is not None:
            header.setdefault(m.group(1), []).append(m.group(2).strip())
    return header


def law_body_hash(path: Path) -> str:
    """SHA-256 (first 12 hex) of LAWS.bend minus its leading comment/blank header.

    Excluding the header is what lets a reviewer append ``# approved:`` (or a
    ``# spec:`` fix) without invalidating the approval; any change to the law
    text itself, whitespace included, changes the digest on purpose.
    """
    lines = _read_lines(path)
    body = "\n".join(lines[_header_end(lines):])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


def valid_approval(header: Dict[str, List[str]], body_hash: str) -> Optional[str]:
    """Return the approval line whose digest matches the current law body, else None.

    Approval lines are append-only: any one well-formed line (valid calendar
    date, approver, 12-hex digest) that matches ``body_hash`` is enough.
    """
    for value in header.get("approved", []):
        m = APPROVED_RE.match(value)
        if m is None or m.group("digest") != body_hash:
            continue
        try:
            datetime.date.fromisoformat(m.group("date"))
        except ValueError:
            continue
        return value
    return None


def declares_laws(path: Path) -> bool:
    """True if LAWS.bend contains at least one ``law`` declaration."""
    return any(LAW_DECL_RE.match(line) for line in _read_lines(path))


def imports_laws(proof_path: Path) -> bool:
    """True if PROOF.bend imports LAWS (any accepted local spelling)."""
    return any(LAWS_IMPORT_RE.match(line.strip()) for line in _read_lines(proof_path))


def _local_import_exists(bend_file: Path, root: Path, target: str) -> bool:
    """True if ``target`` resolves inside ``root`` to an existing ``.bend`` file."""
    resolved = (bend_file.parent / target).resolve()
    if resolved != root and root not in resolved.parents:
        return False
    if resolved.suffix == ".bend":
        candidates = [resolved]
    else:
        candidates = [resolved.with_name(resolved.name + ".bend"), resolved]
    return any(c.is_file() for c in candidates)


def disallowed_imports(laws_dir: Path) -> List[str]:
    """Import lines that fail the allowlist, as ``"<relative file>: <line>"``.

    Allowed: the bundled standard library (``import Base``) and a relative
    ``import`` of a ``.bend`` file that exists inside ``laws_dir``. Everything
    else fails: unknown forms (``from``, aliases, trailing comments), absolute
    paths, Hub namespaces, URLs, paths escaping the directory, and bare names
    with no matching file (which is how a Hub package import would look).
    """
    if not laws_dir.is_dir():
        return []
    root = laws_dir.resolve()
    bad: List[str] = []
    for bend_file in sorted(laws_dir.rglob("*.bend")):
        rel = bend_file.relative_to(laws_dir)
        for raw in _read_lines(bend_file):
            if not IMPORT_LINE_RE.match(raw):
                continue
            line = raw.strip()
            m = LOCAL_IMPORT_RE.match(line)
            if m is None:
                bad.append(f"{rel}: {line}")
                continue
            target = m.group("target")
            if target in STDLIB_IMPORTS:
                continue
            if not _local_import_exists(bend_file, root, target):
                bad.append(f"{rel}: {line}")
    return bad
