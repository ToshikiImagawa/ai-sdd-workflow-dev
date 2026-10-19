"""laws_drafting.py - Deterministic helpers for drafting Bend laws from a spec.

Single source of truth for the laws-drafting conventions (laws-drafting_spec.md):
the spec section hash behind ``# source:`` comments (FR-003), the static checks
on drafted law files (FR-006, 3.1.3), source-drift detection shared by the proof
gate and the post-tool-use hook (FR-011 / FR-013) and the approval validity
verdict that gates the ``model`` stage (FR-007). Everything is stdlib-only and
needs no ``bend`` (NFR-001 / NFR-002).

Approval and content-hash rules stay in laws_header.py; this module reuses them
and adds nothing to the law-body hash.
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from fm_parser import parse_front_matter, split_front_matter
from laws_header import (
    APPROVED_RE,
    HEADER_RE,
    LAW_DECL_RE,
    MODEL_FILE,
    _header_end,
    _read_lines,
    file_disallowed_imports,
    law_body_hash,
    read_header,
    valid_approval,
)

HASH_LEN = 12

HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.*?)\s*#*\s*$")
SECTION_NUMBER_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)*)(?:\.(?=\s|$)|(?=\s|$))")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
SOURCE_RE = re.compile(
    r"^(?P<spec_id>\S+)\s+§(?P<section>\d+(?:\.\d+)*)\s+sha256:(?P<digest>[0-9a-f]{12})$"
)
LAW_NAME_RE = re.compile(r"^\s*law\s+(?P<name>[A-Za-z_][\w]*)\s*:?")
MODEL_API_RE = re.compile(r"^Model\.(?P<fn>[A-Za-z_]\w*)\s*\(")
MODEL_REF_RE = re.compile(r"\bModel\.([A-Za-z_]\w*)")

# Severities / finding codes (stable: consumed by the skill, the gate and the hook).
ERROR = "error"
WARNING = "warning"
SOURCE_DRIFT = "source_drift"
SOURCE_INVALID = "source_invalid"


class SourceRef(NamedTuple):
    """A parsed ``# source: <spec id> §<section> sha256:<digest>`` comment."""
    spec_id: str
    section: str
    digest: str


class LawDecl(NamedTuple):
    """One ``law`` declaration: its name, 1-based line, nearest source comment and body."""
    name: str
    line: int
    source_raw: Optional[str]   # text after "# source:" (None: no source comment)
    source: Optional[SourceRef]  # parsed form (None when absent or malformed)
    body: str                    # whitespace-normalised text after the ``law <name>`` word


class Finding(NamedTuple):
    """A static-check result. ``law`` is "" for file-level findings."""
    code: str
    severity: str
    law: str
    message: str


class ApprovalStatus(NamedTuple):
    """Verdict on a law file's approval line (spec FR-007 refusal reasons).

    ``state`` is one of ``valid`` / ``missing`` (no approval line) /
    ``malformed`` (approval lines exist, none well-formed) / ``mismatch``
    (well-formed but bound to different law text; ``current_hash`` is what to
    approve) / ``no_file``.
    """
    state: str
    current_hash: str
    approval: Optional[str]


# --- section hash ----------------------------------------------------------


def normalize_section(text: str) -> str:
    """Normalise a section body: LF line ends, each line stripped, runs of blank
    lines collapsed to one, leading/trailing blank lines dropped."""
    out: List[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line and (not out or not out[-1]):
            continue
        out.append(line)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def _headings(spec_text: str) -> List[Tuple[int, int, str, str]]:
    """``(line_index, level, number, title)`` for every heading outside the front
    matter and fenced code blocks. ``number`` is "" for an unnumbered heading."""
    _, body = split_front_matter(spec_text)
    lines = body.replace("\r\n", "\n").splitlines()
    result: List[Tuple[int, int, str, str]] = []
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m is None:
            continue
        title = m.group("title")
        n = SECTION_NUMBER_RE.match(title)
        result.append((i, len(m.group("marks")), n.group("num") if n else "", title))
    return result


def find_section(spec_text: str, section: str) -> Optional[str]:
    """Raw body of the section numbered ``section`` (e.g. ``"3.1.1"``), else None.

    A section runs from the line after its heading to just before the next
    heading of the same or a higher level (child sections are included). The
    number is the heading's leading number, a trailing period ignored; the
    first heading with that number wins and unnumbered headings never match.
    """
    section = section.strip().lstrip("§").rstrip(".")
    if not section:
        return None
    _, body = split_front_matter(spec_text)
    lines = body.replace("\r\n", "\n").splitlines()
    headings = _headings(spec_text)
    for idx, (line_no, level, number, _title) in enumerate(headings):
        if number != section:
            continue
        end = len(lines)
        for next_line, next_level, _n, _t in headings[idx + 1:]:
            if next_level <= level:
                end = next_line
                break
        return "\n".join(lines[line_no + 1:end])
    return None


def section_hash(spec_text: str, section: str) -> Optional[str]:
    """sha256 (first 12 hex) of the normalised section body, None if no such section."""
    raw = find_section(spec_text, section)
    if raw is None:
        return None
    return hashlib.sha256(normalize_section(raw).encode("utf-8")).hexdigest()[:HASH_LEN]


def spec_id_of(spec_text: str) -> str:
    """The spec's front matter ``id`` ("" if absent)."""
    fm, _ = split_front_matter(spec_text)
    return str(parse_front_matter(fm).get("id", "")) if fm else ""


def _read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[1:] if text.startswith("﻿") else text


def section_hash_of_file(spec_path: Path, section: str) -> Optional[str]:
    """:func:`section_hash` of a spec file."""
    return section_hash(_read_text(spec_path), section)


# --- law file parsing ------------------------------------------------------


def parse_source(value: str) -> Optional[SourceRef]:
    """Parse the text after ``# source:``; None when it does not match the format."""
    m = SOURCE_RE.match(value.strip())
    if m is None:
        return None
    return SourceRef(m.group("spec_id"), m.group("section"), m.group("digest"))


def _law_body(lines: List[str], start: int) -> str:
    """Text of the law at ``lines[start]`` (without its name), whitespace-normalised.

    The law ends at the next non-blank line that starts in column 0.
    """
    first = LAW_NAME_RE.match(lines[start])
    parts = [lines[start][first.end():] if first else lines[start]]
    for line in lines[start + 1:]:
        if line.strip() and not line[0].isspace():
            break
        parts.append(line)
    return " ".join(" ".join(parts).split())


def parse_laws(path: Path) -> List[LawDecl]:
    """Every ``law`` declaration of a law file with its nearest ``# source:`` comment.

    The source comment is looked up through the blank and comment lines directly
    above the declaration; any code line stops the search.
    """
    lines = _read_lines(path)
    laws: List[LawDecl] = []
    for i, line in enumerate(lines):
        if not LAW_DECL_RE.match(line):
            continue
        name = LAW_NAME_RE.match(line)
        source_raw: Optional[str] = None
        j = i - 1
        while j >= 0 and (not lines[j].strip() or lines[j].lstrip().startswith("#")):
            m = HEADER_RE.match(lines[j].strip())
            if m is not None and m.group(1) == "source":
                source_raw = m.group(2).strip()
                break
            j -= 1
        laws.append(LawDecl(
            name.group("name") if name else "",
            i + 1,
            source_raw,
            parse_source(source_raw) if source_raw is not None else None,
            _law_body(lines, i),
        ))
    return laws


def model_api_functions(path: Path) -> Optional[List[str]]:
    """Function names declared by ``# model-api: Model.<fn>(...)`` lines in the law
    *body* (after the leading comment header, so the lines are hashed and approved).

    None when the body has no ``# model-api:`` line at all.
    """
    lines = _read_lines(path)
    found: Optional[List[str]] = None
    for raw in lines[_header_end(lines):]:
        m = HEADER_RE.match(raw.strip())
        if m is None or m.group(1) != "model-api":
            continue
        found = [] if found is None else found
        a = MODEL_API_RE.match(m.group(2).strip())
        if a is not None:
            found.append(a.group("fn"))
    return found


# --- source drift (gate FR-013 / hook FR-011 / draft check #1) -------------


def _source_problem(law: LawDecl, spec_text: str, spec_id: str) -> Optional[Tuple[str, str]]:
    """``(kind, detail)`` if a law's source disagrees with the spec, else None.

    kind: ``invalid`` (malformed ``# source:``), ``spec`` (names another spec id),
    ``missing`` (section absent), ``hash`` (section changed).
    """
    if law.source_raw is None:
        return None
    ref = law.source
    if ref is None:
        return ("invalid", law.source_raw)
    if spec_id and ref.spec_id != spec_id:
        return ("spec", ref.spec_id)
    current = section_hash(spec_text, ref.section)
    if current is None:
        return ("missing", ref.section)
    if current != ref.digest:
        return ("hash", current)
    return None


def source_drift(laws_path: Path, spec_path: Path) -> List[Dict[str, str]]:
    """FR-013 warnings for ``run-verification.py proof`` and the FR-011 hook.

    One ``{"code": "source_drift"|"source_invalid", "law": <name>, "source":
    <section without §>}`` per law whose ``# source:`` no longer matches the
    spec (section gone, renumbered, changed, or naming another spec id) or is
    malformed. Laws without ``# source:`` (hand-written) are skipped. A malformed
    source carries the raw text in ``source``.
    """
    spec_text = _read_text(spec_path)
    spec_id = spec_id_of(spec_text)
    warnings: List[Dict[str, str]] = []
    for law in parse_laws(laws_path):
        problem = _source_problem(law, spec_text, spec_id)
        if problem is None:
            continue
        if problem[0] == "invalid":
            warnings.append({"code": SOURCE_INVALID, "law": law.name, "source": problem[1]})
        else:
            section = law.source.section if law.source else ""
            warnings.append({"code": SOURCE_DRIFT, "law": law.name, "source": section})
    return warnings


# --- static checks (3.1.3) -------------------------------------------------


def _top_level_equations(body: str) -> List[Tuple[str, str]]:
    """``(lhs, rhs)`` of each ``{lhs == rhs : T}`` group opened at depth 0, with the
    ``: T`` annotation and whitespace removed. Groups without a depth-1 ``==`` are skipped."""
    pairs: List[Tuple[str, str]] = []
    depth = 0
    start = -1
    for i, ch in enumerate(body):
        if ch in "([{":
            if depth == 0 and ch == "{":
                start = i + 1
            depth += 1
        elif ch in ")]}":
            depth = max(depth - 1, 0)
            if depth == 0 and ch == "}" and start >= 0:
                pair = _split_equation(body[start:i])
                if pair is not None:
                    pairs.append(pair)
                start = -1
    return pairs


def _split_equation(group: str) -> Optional[Tuple[str, str]]:
    depth = 0
    eq = -1
    colon = -1
    for i, ch in enumerate(group):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth == 0 and group.startswith("==", i) and eq < 0:
            eq = i
        elif depth == 0 and ch == ":" and eq >= 0:
            colon = i
    if eq < 0:
        return None
    rhs_end = colon if colon > eq else len(group)
    squash = lambda s: "".join(s.split())  # noqa: E731
    return squash(group[:eq]), squash(group[eq + 2:rhs_end])


def static_check(
    laws_path: Path,
    spec_path: Optional[Path] = None,
    *,
    tolerate_missing_model: bool = True,
) -> List[Finding]:
    """Static checks of a ``draft`` output (``LAWS.bend`` / ``LAWS.draft.bend``).

    ``bend`` is not needed. Applies only to drafted files (hand-written laws
    lack ``# source:`` by design). Errors: 2 missing ``# source:``; 1 section
    absent / section hash differs from the spec / source naming another spec
    id / malformed source; 5 disallowed import; ``# model-api:`` missing or
    out of step with the ``Model.*`` references. Warnings: 3 duplicate bodies;
    4 trivial (both sides identical) laws. Without ``spec_path`` the source
    checks (1) are skipped.
    """
    findings: List[Finding] = []
    laws = parse_laws(laws_path)
    spec_text = _read_text(spec_path) if spec_path is not None else None
    spec_id = spec_id_of(spec_text) if spec_text is not None else ""

    for law in laws:
        if law.source_raw is None:
            findings.append(Finding(
                "source_missing", ERROR, law.name, f"law '{law.name}' has no '# source:' comment"))
            continue
        if spec_text is None:
            continue
        problem = _source_problem(law, spec_text, spec_id)
        if problem is None:
            continue
        kind, detail = problem
        text = {
            "invalid": f"malformed '# source:' ({detail})",
            "spec": f"'# source:' names spec id '{detail}', not '{spec_id}'",
            "missing": f"section §{detail} does not exist in the spec",
            "hash": f"section hash differs from the spec (current sha256:{detail})",
        }[kind]
        code = {"invalid": SOURCE_INVALID, "spec": "source_spec_mismatch",
                "missing": "source_section_missing", "hash": SOURCE_DRIFT}[kind]
        findings.append(Finding(code, ERROR, law.name, f"law '{law.name}': {text}"))

    seen: Dict[str, str] = {}
    for law in laws:
        if law.body in seen:
            findings.append(Finding(
                "duplicate_law", WARNING, law.name,
                f"law '{law.name}' has the same body as '{seen[law.body]}'"))
        else:
            seen[law.body] = law.name
        if any(lhs == rhs for lhs, rhs in _top_level_equations(law.body)):
            findings.append(Finding(
                "trivial_law", WARNING, law.name,
                f"law '{law.name}' is trivially true (both sides of '==' are identical)"))

    root = laws_path.parent.resolve()
    tolerated = [f"./{MODEL_FILE}", MODEL_FILE] if tolerate_missing_model else []
    for line in file_disallowed_imports(laws_path, root, tolerated):
        findings.append(Finding("import_disallowed", ERROR, "", f"import not allowed: {line}"))

    findings.extend(_model_api_findings(laws_path, laws))
    return findings


def _model_api_findings(laws_path: Path, laws: List[LawDecl]) -> List[Finding]:
    referenced = sorted({fn for law in laws for fn in MODEL_REF_RE.findall(law.body)})
    declared = model_api_functions(laws_path)
    if not referenced and declared is None:
        return []
    if declared is None:
        hint = ""
        if "model-api" in read_header(laws_path):
            hint = " (found only in the leading comment header, which is not hashed or approved)"
        return [Finding(
            "model_api_missing", ERROR, "",
            "laws reference Model." + ", Model.".join(referenced)
            + f" but the body has no '# model-api:' line{hint}")]
    out: List[Finding] = []
    for fn in sorted(set(referenced) - set(declared)):
        out.append(Finding(
            "model_api_mismatch", ERROR, "",
            f"Model.{fn} is referenced by a law but not declared in '# model-api:'"))
    for fn in sorted(set(declared) - set(referenced)):
        out.append(Finding(
            "model_api_mismatch", ERROR, "",
            f"Model.{fn} is declared in '# model-api:' but no law references it"))
    return out


def has_errors(findings: List[Finding]) -> bool:
    """True if any finding is an error (FR-006: then ``drafted`` is not proposed)."""
    return any(f.severity == ERROR for f in findings)


# --- approval validity (FR-007) --------------------------------------------


def approval_status(laws_path: Path) -> ApprovalStatus:
    """Is the approval line of ``laws_path`` valid for its current law body?

    Reuses ``law_body_hash`` / ``valid_approval`` (laws_header.py). ``mismatch``
    and ``current_hash`` give the ``model`` stage its refusal reason and the
    hash to show the approver.
    """
    if not laws_path.is_file():
        return ApprovalStatus("no_file", "", None)
    current = law_body_hash(laws_path)
    values = read_header(laws_path).get("approved", [])
    if not values:
        return ApprovalStatus("missing", current, None)
    valid = valid_approval({"approved": values}, current)
    if valid is not None:
        return ApprovalStatus("valid", current, valid)
    for value in values:
        m = APPROVED_RE.match(value)
        # Same line, bound to its own digest: only a malformed date is left to fail.
        if m is not None and valid_approval({"approved": [value]}, m.group("digest")):
            return ApprovalStatus("mismatch", current, value)
    return ApprovalStatus("malformed", current, None)

