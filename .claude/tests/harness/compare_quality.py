#!/usr/bin/env python3
"""compare_quality.py - Issue #16 Step1 accuracy/precision quality comparison.

Compares structured findings from off (baseline) vs on (index) trials to
measure whether the index path produces equivalent or degraded analysis quality.

The prompt asks the consumer to emit a ```json:findings block at the end of its
response. This script parses those blocks from each trial's .out file and
computes:

  1. Document coverage: which .sdd files were analyzed (off ∩ on / off ∪ on)
  2. Feature coverage: which features were analyzed
  3. Finding-level precision/recall/F1 (off = ground truth):
     - Match key = (feature, category, severity, sorted ids_involved)
     - Precision = |on ∩ off| / |on|   (how many of on's findings are real)
     - Recall    = |on ∩ off| / |off|   (how many of off's findings were found)
  4. Per-category breakdown (id_coverage, data_model, api, terminology)
  5. Severity distribution comparison
  6. Qualitative diff: findings only in off (missed by on) / only in on (novel)

Usage:
  python3 compare_quality.py --run-dir .claude/tests/runs/<RUN_ID>
  python3 compare_quality.py --off-file off_1.out --on-file on_1.out
"""

import argparse
import glob
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


def extract_findings_json(text: str) -> Optional[List[Dict[str, Any]]]:
    """Extract the ```json:findings block from a response."""
    # try ```json:findings first, then plain ```json after "findings" header
    patterns = [
        r"```json:findings\s*\n(.*?)```",
        r"```json\s*\n(\[\s*\{.*?\}\s*\]\s*)```",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, ValueError):
                continue
    return None


def extract_files_referenced(text: str) -> Set[str]:
    """Extract .sdd file paths mentioned in the response."""
    paths = set()
    for m in re.finditer(r"(?:requirement|specification)/[\w/.-]+\.md", text):
        paths.add(m.group(0))
    return paths


def finding_key(f: Dict[str, Any]) -> Tuple:
    """Normalized matching key for a finding."""
    return (
        f.get("feature", "").lower().strip(),
        f.get("category", "").lower().strip(),
        f.get("severity", "").lower().strip(),
        tuple(sorted(set(f.get("ids_involved", [])))),
    )


def finding_key_relaxed(f: Dict[str, Any]) -> Tuple:
    """Relaxed key: ignores severity (matches on feature+category+ids)."""
    return (
        f.get("feature", "").lower().strip(),
        f.get("category", "").lower().strip(),
        tuple(sorted(set(f.get("ids_involved", [])))),
    )


def finding_key_overlap(f: Dict[str, Any]) -> Tuple:
    """Overlap key: matches if feature+category match and ids_involved OVERLAP
    (non-empty intersection). Returns (feature, category) for grouping; actual
    overlap check is done in _match_overlap().
    """
    return (
        f.get("feature", "").lower().strip(),
        f.get("category", "").lower().strip(),
    )


def _match_overlap(off_findings: List[Dict], on_findings: List[Dict]) -> Tuple[int, int, int]:
    """Match findings where feature+category match AND ids_involved overlap.
    Returns (matched_off, matched_on, total_overlap_pairs).
    Off findings are consumed greedily (each off finding matches at most one on).
    """
    from collections import defaultdict
    on_by_fc = defaultdict(list)
    for i, f in enumerate(on_findings):
        on_by_fc[finding_key_overlap(f)].append((i, set(f.get("ids_involved", []))))

    matched_off = set()
    matched_on = set()
    for off_f in off_findings:
        fc = finding_key_overlap(off_f)
        off_ids = set(off_f.get("ids_involved", []))
        if not off_ids:
            continue
        for on_i, on_ids in on_by_fc.get(fc, []):
            if on_i in matched_on:
                continue
            if off_ids & on_ids:  # non-empty intersection
                matched_off.add(id(off_f))
                matched_on.add(on_i)
                break
    return len(matched_off), len(matched_on), min(len(matched_off), len(matched_on))


def load_trial(path: str) -> Dict[str, Any]:
    """Load a trial .out file and extract structured data."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    findings = extract_findings_json(text)
    files = extract_files_referenced(text)
    features = set()
    if findings:
        for fd in findings:
            feat = fd.get("feature", "")
            if feat:
                features.add(feat.lower().strip())
    return {
        "path": path,
        "text_len": len(text),
        "findings": findings or [],
        "findings_count": len(findings) if findings else 0,
        "files_referenced": files,
        "features": features,
        "has_structured_output": findings is not None,
    }


def compare_pair(off: Dict[str, Any], on: Dict[str, Any]) -> Dict[str, Any]:
    """Compare one off trial vs one on trial."""
    result: Dict[str, Any] = {
        "off_file": off["path"],
        "on_file": on["path"],
        "off_has_structured": off["has_structured_output"],
        "on_has_structured": on["has_structured_output"],
    }

    # Document coverage
    off_files = off["files_referenced"]
    on_files = on["files_referenced"]
    union = off_files | on_files
    intersection = off_files & on_files
    result["document_coverage"] = {
        "off_files": len(off_files),
        "on_files": len(on_files),
        "intersection": len(intersection),
        "union": len(union),
        "jaccard": len(intersection) / len(union) if union else 1.0,
        "only_in_off": sorted(off_files - on_files),
        "only_in_on": sorted(on_files - off_files),
    }

    # Feature coverage
    result["feature_coverage"] = {
        "off_features": sorted(off["features"]),
        "on_features": sorted(on["features"]),
        "off_only": sorted(off["features"] - on["features"]),
        "on_only": sorted(on["features"] - off["features"]),
    }

    if not off["has_structured_output"] or not on["has_structured_output"]:
        result["finding_comparison"] = {
            "error": "structured findings not available in one or both trials",
            "off_has_structured": off["has_structured_output"],
            "on_has_structured": on["has_structured_output"],
        }
        return result

    off_findings = off["findings"]
    on_findings = on["findings"]

    # Filter out info-severity for precision/recall (info = not a defect)
    off_defects = [f for f in off_findings if f.get("severity", "").lower() != "info"]
    on_defects = [f for f in on_findings if f.get("severity", "").lower() != "info"]

    # Strict matching
    off_keys = set(finding_key(f) for f in off_defects)
    on_keys = set(finding_key(f) for f in on_defects)
    strict_tp = off_keys & on_keys
    strict_precision = len(strict_tp) / len(on_keys) if on_keys else 1.0
    strict_recall = len(strict_tp) / len(off_keys) if off_keys else 1.0
    strict_f1 = (2 * strict_precision * strict_recall / (strict_precision + strict_recall)
                 if (strict_precision + strict_recall) > 0 else 0.0)

    # Relaxed matching (ignore severity)
    off_keys_r = set(finding_key_relaxed(f) for f in off_defects)
    on_keys_r = set(finding_key_relaxed(f) for f in on_defects)
    relaxed_tp = off_keys_r & on_keys_r
    relaxed_precision = len(relaxed_tp) / len(on_keys_r) if on_keys_r else 1.0
    relaxed_recall = len(relaxed_tp) / len(off_keys_r) if off_keys_r else 1.0
    relaxed_f1 = (2 * relaxed_precision * relaxed_recall / (relaxed_precision + relaxed_recall)
                  if (relaxed_precision + relaxed_recall) > 0 else 0.0)

    # Per-category breakdown
    categories = sorted(set(
        f.get("category", "unknown").lower() for f in off_defects + on_defects
    ))
    per_category = {}
    for cat in categories:
        off_cat = set(finding_key(f) for f in off_defects if f.get("category", "").lower() == cat)
        on_cat = set(finding_key(f) for f in on_defects if f.get("category", "").lower() == cat)
        tp = off_cat & on_cat
        per_category[cat] = {
            "off_count": len(off_cat),
            "on_count": len(on_cat),
            "matched": len(tp),
            "precision": len(tp) / len(on_cat) if on_cat else 1.0,
            "recall": len(tp) / len(off_cat) if off_cat else 1.0,
        }

    # Severity distribution
    off_sev = {}
    on_sev = {}
    for f in off_findings:
        s = f.get("severity", "unknown").lower()
        off_sev[s] = off_sev.get(s, 0) + 1
    for f in on_findings:
        s = f.get("severity", "unknown").lower()
        on_sev[s] = on_sev.get(s, 0) + 1

    # Qualitative diff: findings only in off (missed) / only in on (novel)
    missed = [f for f in off_defects if finding_key(f) not in on_keys]
    novel = [f for f in on_defects if finding_key(f) not in off_keys]

    # Overlap matching: feature+category match AND ids overlap (most realistic)
    overlap_off, overlap_on, overlap_tp = _match_overlap(off_defects, on_defects)
    overlap_precision = overlap_on / len(on_defects) if on_defects else 1.0
    overlap_recall = overlap_off / len(off_defects) if off_defects else 1.0
    overlap_f1 = (2 * overlap_precision * overlap_recall / (overlap_precision + overlap_recall)
                  if (overlap_precision + overlap_recall) > 0 else 0.0)

    result["finding_comparison"] = {
        "off_total": len(off_findings),
        "on_total": len(on_findings),
        "off_defects": len(off_defects),
        "on_defects": len(on_defects),
        "overlap": {
            "precision": round(overlap_precision, 4),
            "recall": round(overlap_recall, 4),
            "f1": round(overlap_f1, 4),
            "matched_off": overlap_off,
            "matched_on": overlap_on,
        },
        "strict": {
            "precision": round(strict_precision, 4),
            "recall": round(strict_recall, 4),
            "f1": round(strict_f1, 4),
            "true_positive": len(strict_tp),
        },
        "relaxed": {
            "precision": round(relaxed_precision, 4),
            "recall": round(relaxed_recall, 4),
            "f1": round(relaxed_f1, 4),
            "true_positive": len(relaxed_tp),
        },
        "per_category": per_category,
        "severity_distribution": {"off": off_sev, "on": on_sev},
        "missed_by_on": [{
            "feature": f.get("feature"), "category": f.get("category"),
            "severity": f.get("severity"), "detail": f.get("detail", "")[:200],
            "ids": f.get("ids_involved", []),
        } for f in missed],
        "novel_in_on": [{
            "feature": f.get("feature"), "category": f.get("category"),
            "severity": f.get("severity"), "detail": f.get("detail", "")[:200],
            "ids": f.get("ids_involved", []),
        } for f in novel],
    }

    return result


def aggregate_pairs(pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate comparison results across N trial pairs."""
    n = len(pairs)
    if n == 0:
        return {"error": "no pairs to aggregate"}

    valid = [p for p in pairs if "finding_comparison" in p
             and "error" not in p["finding_comparison"]]
    if not valid:
        return {
            "total_pairs": n,
            "valid_pairs": 0,
            "error": "no valid structured pairs",
        }

    def med(vals):
        vals = sorted(vals)
        mid = len(vals) // 2
        return vals[mid] if vals else 0

    overlap_p = [p["finding_comparison"]["overlap"]["precision"] for p in valid]
    overlap_r = [p["finding_comparison"]["overlap"]["recall"] for p in valid]
    overlap_f = [p["finding_comparison"]["overlap"]["f1"] for p in valid]
    strict_p = [p["finding_comparison"]["strict"]["precision"] for p in valid]
    strict_r = [p["finding_comparison"]["strict"]["recall"] for p in valid]
    strict_f = [p["finding_comparison"]["strict"]["f1"] for p in valid]
    relaxed_p = [p["finding_comparison"]["relaxed"]["precision"] for p in valid]
    relaxed_r = [p["finding_comparison"]["relaxed"]["recall"] for p in valid]
    relaxed_f = [p["finding_comparison"]["relaxed"]["f1"] for p in valid]
    jaccards = [p["document_coverage"]["jaccard"] for p in valid]
    total_missed = sum(len(p["finding_comparison"]["missed_by_on"]) for p in valid)
    total_novel = sum(len(p["finding_comparison"]["novel_in_on"]) for p in valid)

    return {
        "total_pairs": n,
        "valid_pairs": len(valid),
        "document_coverage_jaccard_median": round(med(jaccards), 4),
        "overlap": {
            "precision_median": round(med(overlap_p), 4),
            "recall_median": round(med(overlap_r), 4),
            "f1_median": round(med(overlap_f), 4),
        },
        "strict": {
            "precision_median": round(med(strict_p), 4),
            "recall_median": round(med(strict_r), 4),
            "f1_median": round(med(strict_f), 4),
        },
        "relaxed": {
            "precision_median": round(med(relaxed_p), 4),
            "recall_median": round(med(relaxed_r), 4),
            "f1_median": round(med(relaxed_f), 4),
        },
        "total_missed_by_on": total_missed,
        "total_novel_in_on": total_novel,
    }


def write_report(agg: Dict[str, Any], pairs: List[Dict[str, Any]], out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "quality_result.json"), "w", encoding="utf-8") as f:
        json.dump({"aggregate": agg, "pairs": pairs}, f, ensure_ascii=False, indent=2)

    lines = ["# Issue #16 Step1 — Quality Comparison (off vs on)", ""]
    lines.append(f"- pairs: {agg.get('total_pairs')} total, {agg.get('valid_pairs')} with structured findings")
    lines.append(f"- document coverage (Jaccard) median: {agg.get('document_coverage_jaccard_median')}")
    lines.append("")
    if "overlap" in agg:
        lines.append("## Finding-level accuracy (off = ground truth)")
        lines.append("")
        lines.append("| Matching | Precision | Recall | F1 |")
        lines.append("|:--|:--|:--|:--|")
        o = agg["overlap"]
        lines.append(f"| **Overlap** (feature+category match, ids overlap) | {o['precision_median']} | {o['recall_median']} | {o['f1_median']} |")
        s = agg["strict"]
        lines.append(f"| **Strict** (feature+category+severity+ids exact) | {s['precision_median']} | {s['recall_median']} | {s['f1_median']} |")
        r = agg["relaxed"]
        lines.append(f"| **Relaxed** (feature+category+ids exact, ignore severity) | {r['precision_median']} | {r['recall_median']} | {r['f1_median']} |")
        lines.append("")
        lines.append(f"- total findings missed by on (across all pairs): {agg.get('total_missed_by_on')}")
        lines.append(f"- total novel findings in on (not in off): {agg.get('total_novel_in_on')}")

    # per-pair detail: missed/novel
    for i, p in enumerate(pairs):
        fc = p.get("finding_comparison", {})
        if "error" in fc:
            lines.append(f"\n### Pair {i+1}: {fc['error']}")
            continue
        lines.append(f"\n### Pair {i+1}")
        lines.append(f"- off: {fc['off_defects']} defects, on: {fc['on_defects']} defects")
        lines.append(f"- strict P/R/F1: {fc['strict']['precision']}/{fc['strict']['recall']}/{fc['strict']['f1']}")
        if fc["missed_by_on"]:
            lines.append("- **Missed by on** (false negatives):")
            for m in fc["missed_by_on"]:
                lines.append(f"  - [{m['category']}] {m['feature']}: {m['detail'][:120]}")
        if fc["novel_in_on"]:
            lines.append("- **Novel in on** (not in off baseline):")
            for m in fc["novel_in_on"]:
                lines.append(f"  - [{m['category']}] {m['feature']}: {m['detail'][:120]}")

    lines.append("")
    with open(os.path.join(out_dir, "quality_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare off vs on quality.")
    parser.add_argument("--run-dir", default="", help="run directory (finds off_*.out/on_*.out)")
    parser.add_argument("--off-file", default="", help="single off trial output")
    parser.add_argument("--on-file", default="", help="single on trial output")
    parser.add_argument("--out-dir", default="", help="output dir (default: run-dir)")
    args = parser.parse_args()

    pairs_data: List[Tuple[str, str]] = []
    if args.run_dir:
        offs = sorted(glob.glob(os.path.join(args.run_dir, "off_*.out")))
        ons = sorted(glob.glob(os.path.join(args.run_dir, "on_*.out")))
        for o, n in zip(offs, ons):
            pairs_data.append((o, n))
    elif args.off_file and args.on_file:
        pairs_data.append((args.off_file, args.on_file))
    else:
        parser.error("provide --run-dir or --off-file/--on-file")

    pairs = []
    for off_path, on_path in pairs_data:
        off = load_trial(off_path)
        on = load_trial(on_path)
        pairs.append(compare_pair(off, on))

    agg = aggregate_pairs(pairs)
    out_dir = args.out_dir or args.run_dir or "."
    write_report(agg, pairs, out_dir)

    print(json.dumps(agg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
