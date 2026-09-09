#!/usr/bin/env python3
"""Script-side grading for the assertions that can be decided mechanically.

iteration-1 measured a 20pt noise floor: the control skill (byte-identical on both branches)
produced a fake +20pt "improvement". Two things feed that noise -- variance between runs, and
variance between graders. This module removes the second one for every assertion whose verdict
is a fact rather than a judgement: does a cited line actually say what the run claims, is an
attribute present on every requirement, was a pre-existing manual note preserved.

Assertions like "did it leave the decision to a human" stay with the agent grader; they are
judgements and pretending otherwise would trade grader noise for parser noise.

**Coverage is 4 of 20 assertions, not more.** Eight were attempted against iteration-1's runs
and four had to be handed back, each for a reason worth remembering:

- `run-checklist` "exit code recorded per item": the record sits near the item id, not on its
  line, so the check needed a text window -- and the verdict then depended on the window size.
  A check whose answer moves with a tuning constant is not a measurement.
- `run-checklist` "pre-existing manual note preserved": a substring test said PASS on a run
  that had written *"the old note ... was removed as unreproducible and replaced"* -- quoting
  the note while deleting it. Presence of the text and preservation of the record are
  different propositions, and only the second one is the assertion.
- `doc-consistency-checker` "citations resolve" / "findings stay in scope": runs cite as
  "`sdd-init_spec.md` の FR-005" or "spec 174 行目", not `path:line`. Three of four runs were
  unparseable. Building a parser for free-form prose would just relocate the noise.

Honesty rule: when a check cannot parse what it needs, it returns UNPARSEABLE rather than a
verdict. A silently-wrong `false` is worse than an admitted gap, because the whole point of
mechanizing is to stop the measurement from drifting.

Usage:
    grade.py <run-dir> --skill <name> [--json]

Reads <run-dir>/RUN_OUTPUT.md plus whatever files the checks need, and prints one line per
mechanizable assertion (or JSON with --json) shaped like the `expectations` entries the
aggregator consumes.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

UNPARSEABLE = "UNPARSEABLE"

# Requirement IDs as they appear in this project: PRD level uses underscores
# (UR_001 / FR_001_02), spec level uses hyphens (FR-001). Both shapes are matched here so a
# run that picked the wrong one is still parsed -- and then failed by the convention check.
ID_RE = re.compile(r"\b(UR|FR|NFR|IR|DC)[_-]\d{3}(?:_\d{2})?\b")

# A markdown table row whose first cell is a requirement ID is a definition row. Narrative
# mentions of an ID elsewhere are not, which is why rows are matched instead of bare IDs.
TABLE_ROW_RE = re.compile(r"^\s*\|\s*\**\s*((?:UR|FR|NFR|IR|DC)[_-]\d{3}(?:_\d{2})?)\s*\**\s*\|")

ATTR_COLUMNS = {
    "priority": ("priority", "優先度", "優先"),
    "risk": ("risk", "リスク"),
    "verification": ("verification", "検証方法", "検証手段", "検証"),
}

def read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def split_tables(text: str) -> List[Tuple[List[str], List[List[str]]]]:
    """Return (header cells, data rows) for every markdown table containing an ID row."""
    tables: List[Tuple[List[str], List[List[str]]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            i += 1
            continue
        block = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            block.append(lines[i])
            i += 1
        if len(block) < 2:
            continue
        cells = [[c.strip() for c in row.strip().strip("|").split("|")] for row in block]
        header = cells[0]
        # Row 1 is the |---|---| separator in a well-formed table.
        body = [r for r in cells[1:] if not all(set(c) <= set("-: ") for c in r)]
        if any(TABLE_ROW_RE.match(f"|{r[0]}|") for r in body if r):
            tables.append((header, body))
    return tables


def find_attr_columns(header: List[str]) -> Dict[str, Optional[int]]:
    found: Dict[str, Optional[int]] = {}
    lowered = [h.lower() for h in header]
    for attr, needles in ATTR_COLUMNS.items():
        idx = None
        for n, cell in enumerate(lowered):
            if any(needle in cell for needle in needles):
                idx = n
                break
        found[attr] = idx
    return found


# --------------------------------------------------------------------------- checks


def check_id_conventions(run_dir: Path) -> Dict:
    """analyze-requirements A3: IDs unique, consecutive, and matching id_conventions."""
    out = read_text(run_dir / "RUN_OUTPUT.md")
    config = read_text(run_dir / ".sdd-config.json")
    if out is None or config is None:
        return {"passed": UNPARSEABLE, "evidence": "RUN_OUTPUT.md か .sdd-config.json を読めない"}
    conventions = json.loads(config).get("id_conventions", {})
    patterns = {
        "UR": conventions.get("prd_user"),
        "FR": conventions.get("prd_functional"),
        "NFR": conventions.get("prd_nonfunctional"),
        "IR": conventions.get("prd_interface"),
        "DC": conventions.get("prd_constraint"),
    }

    # An ID legitimately appears in several tables (definition table, traceability table,
    # summary). Uniqueness is therefore a per-table property, not a document-wide one --
    # counting across tables flags every ID in a well-formed document.
    problems: List[str] = []
    defined: List[str] = []
    for _header, body in split_tables(out):
        ids_here: List[str] = []
        for row in body:
            m = TABLE_ROW_RE.match(f"|{row[0]}|")
            if m:
                ids_here.append(m.group(1))
        dupes = sorted({i for i in ids_here if ids_here.count(i) > 1})
        if dupes:
            problems.append(f"同一表内の重複 ID: {', '.join(dupes)}")
        defined.extend(ids_here)
    if not defined:
        return {"passed": UNPARSEABLE, "evidence": "要求定義表を検出できなかった"}

    for rid in sorted(set(defined)):
        kind = ID_RE.match(rid).group(1)
        pat = patterns.get(kind)
        if not pat:
            continue
        if not re.match(pat, rid):
            problems.append(f"{rid} が id_conventions（{kind}: {pat}）に不適合")

    # Consecutiveness is checked per kind on the top-level number only; sub-IDs like
    # FR_001_02 hang off their parent and do not form their own sequence.
    by_kind: Dict[str, List[int]] = {}
    for rid in set(defined):
        m = re.match(r"(UR|FR|NFR|IR|DC)[_-](\d{3})$", rid)
        if m:
            by_kind.setdefault(m.group(1), []).append(int(m.group(2)))
    for kind, nums in by_kind.items():
        nums.sort()
        if nums and nums != list(range(1, len(nums) + 1)):
            problems.append(f"{kind} の連番が不連続: {nums}")

    return {
        "passed": not problems,
        "evidence": (
            f"検出した定義 ID {len(set(defined))} 件: {', '.join(sorted(set(defined)))}. "
            + ("; ".join(problems) if problems else "重複・不適合・欠番なし")
        ),
    }


def check_attributes_present(run_dir: Path) -> Dict:
    """analyze-requirements A4: Priority / Risk / Verification on every requirement."""
    out = read_text(run_dir / "RUN_OUTPUT.md")
    if out is None:
        return {"passed": UNPARSEABLE, "evidence": "RUN_OUTPUT.md を読めない"}

    tables = split_tables(out)
    if not tables:
        return {"passed": UNPARSEABLE, "evidence": "要求定義表を検出できなかった"}

    missing: List[str] = []
    counted = 0
    for header, body in tables:
        cols = find_attr_columns(header)
        # Traceability and summary tables carry IDs but no attribute columns. Checking them
        # would report every requirement as missing all three attributes, so only tables
        # that actually define attributes are in scope.
        if not any(idx is not None for idx in cols.values()):
            continue
        for row in body:
            m = TABLE_ROW_RE.match(f"|{row[0]}|")
            if not m:
                continue
            counted += 1
            rid = m.group(1)
            kind = ID_RE.match(rid).group(1)
            for attr, idx in cols.items():
                # Verification is a property of what gets verified -- functional and
                # non-functional requirements. User requirements sit above that level, and
                # this project's own PRD template does not give them a verification column.
                if attr == "verification" and kind not in {"FR", "NFR"}:
                    continue
                if idx is None:
                    missing.append(f"{rid}: {attr} 列が表に無い")
                elif idx >= len(row) or not row[idx] or row[idx] in {"-", "—", "N/A"}:
                    missing.append(f"{rid}: {attr} が空")

    if counted == 0:
        return {"passed": UNPARSEABLE, "evidence": "属性列を持つ要求定義表を検出できなかった"}
    return {
        "passed": not missing,
        "evidence": f"要求行 {counted} 件を検査. " + ("; ".join(missing[:12]) if missing else "3属性すべて付与"),
    }










def check_temp_log_removed(run_dir: Path) -> Dict:
    """task-cleanup A2: the temporary log is gone and its noise did not migrate."""
    task_dir = run_dir / ".sdd/task/9004"
    if task_dir.exists() and any(task_dir.iterdir()):
        return {"passed": False, "evidence": f".sdd/task/9004/ が残存: {[p.name for p in task_dir.iterdir()]}"}

    # The timestamps below are unique to the scenario's progress noise, so finding them in a
    # persistent document means the noise was promoted rather than dropped.
    noise = ["14:10", "15:40", "16:20", "17:05", "10:30", "13:50", "14:00"]
    hits = []
    for path in (run_dir / ".sdd").rglob("*.md"):
        if "/task/" in str(path):
            continue
        text = read_text(path) or ""
        for n in noise:
            if n in text:
                hits.append(f"{path.relative_to(run_dir)}: 「{n}」")
    return {
        "passed": not hits,
        "evidence": ".sdd/task/9004/ は削除済. " + ("; ".join(hits[:8]) if hits else "進捗ノイズの昇格なし"),
    }


def check_ticket_traceable(run_dir: Path) -> Dict:
    """task-cleanup A4: the ticket id survives in a persistent document."""
    hits = []
    for path in (run_dir / ".sdd").rglob("*.md"):
        if "/task/" in str(path):
            continue
        text = read_text(path) or ""
        if "9004" in text:
            line = next((l.strip() for l in text.splitlines() if "9004" in l), "")
            hits.append(f"{path.relative_to(run_dir)}: {line[:100]}")
    return {
        "passed": bool(hits),
        "evidence": ("; ".join(hits[:5]) if hits else "永続ドキュメントに `9004` が見つからない"),
    }


# Assertion index (1-based, matching evals.json order) -> check callable.
CHECKS = {
    "analyze-requirements": {
        3: check_id_conventions,
        4: check_attributes_present,
    },
    "task-cleanup": {
        2: check_temp_log_removed,
        4: check_ticket_traceable,
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir")
    parser.add_argument("--skill", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    checks = CHECKS.get(args.skill)
    if checks is None:
        print(f"ERROR: {args.skill} に機械検査は定義されていない", file=sys.stderr)
        return 1

    evals_path = Path(__file__).parent / args.skill / "evals.json"
    assertions = json.loads(evals_path.read_text(encoding="utf-8"))["evals"][0]["assertions"]

    results = []
    for idx, fn in sorted(checks.items()):
        verdict = fn(run_dir)
        results.append(
            {
                "index": idx,
                "text": assertions[idx - 1]["text"],
                "passed": verdict["passed"],
                "evidence": verdict["evidence"],
                "checked_by": "script (grade.py)",
            }
        )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = {True: "PASS", False: "FAIL", UNPARSEABLE: "????"}[r["passed"]]
            print(f"A{r['index']} [{mark}] {r['evidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
