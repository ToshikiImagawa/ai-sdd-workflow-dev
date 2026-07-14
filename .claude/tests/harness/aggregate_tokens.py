#!/usr/bin/env python3
"""aggregate_tokens.py - Issue #16 Step1 A/B token aggregator (2-project design).

The off and on groups run in SEPARATE projects (separate cwd => separate
transcript project-key directory). The group is therefore decided by which
project directory a transcript belongs to — not by an env flag inside one shared
directory. This aggregator collects each group's transcripts from its own
project-key dir and compares `.sdd/` tool_result token cost.

Primary indicator (pre-registered):
  Per-trial (per-session) sum of tokens in tool_result content from Read/Glob/Grep
  calls targeting `.sdd/` (excluding `.sdd/.cache/`), main + sidechain, then the
  median across trials in each group. cache_read is NEVER added.

Secondary: non-cached input (input_tokens + cache_creation_input_tokens);
requirement-ID completeness (quality).

Modes:
  --manifest <path>              A/B mode (reads off/on project_dir + sessions)
  --off-dir <d> --on-dir <d>     A/B mode without a manifest (all sessions)
  --project-dir <d>              dry-run: one "all" group (parser self-check)

Token counting uses tokenizer.Tokenizer (real backend only). Without a backend
the verdict is "inconclusive"; char/byte sums are sanity references only.
"""

import argparse
import glob
import json
import os
import re
import statistics
import sys
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tokenizer import Tokenizer  # noqa: E402

REQ_ID_RE = re.compile(r"\b(?:UR|FR|NFR|DC|IR|PR|REQ)[-_]\d{3}(?:_\d{2})*\b")


def project_key_for(path: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", os.path.abspath(path))


def key_dir_for(project_dir: str) -> str:
    return os.path.join(os.path.expanduser("~/.claude/projects"), project_key_for(project_dir))


def collect_jsonl(key_dir: str) -> List[str]:
    files = glob.glob(os.path.join(key_dir, "*.jsonl"))
    files += glob.glob(os.path.join(key_dir, "*", "subagents", "agent-*.jsonl"))
    files += glob.glob(os.path.join(key_dir, "agent-*.jsonl"))
    return sorted(set(files))


def iter_records(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return


def classify_target(name: str, inp: Dict[str, Any]) -> Optional[str]:
    """Return 'index', 'raw', or None for a tool call based on its target path."""
    if not isinstance(inp, dict):
        return None
    paths: List[str] = []
    if name == "Read":
        paths.append(str(inp.get("file_path", "")))
    elif name == "Glob":
        paths += [str(inp.get("path", "")), str(inp.get("pattern", ""))]
    elif name == "Grep":
        paths += [str(inp.get("path", "")), str(inp.get("glob", ""))]
    else:
        return None
    joined = " ".join(paths)
    if "/.cache/index." in joined or ".sdd/.cache/index." in joined:
        return "index"
    if "/.cache/" in joined and ".sdd" in joined:
        return None
    if ".sdd/" in joined or joined.rstrip().endswith(".sdd") or "/.sdd" in joined:
        return "raw"
    return None


def build_tool_use_index(files: List[str]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for path in files:
        for rec in iter_records(path):
            if rec.get("type") != "assistant":
                continue
            content = rec.get("message", {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    index[block.get("id", "")] = {
                        "name": block.get("name", ""),
                        "input": block.get("input", {}),
                    }
    return index


def result_text(rec: Dict[str, Any]) -> Tuple[str, Optional[int], Optional[str]]:
    """(inline_text, persisted_bytes_or_None, tool_use_id) for a tool_result record.
    inline_text is what the model actually consumed."""
    texts: List[str] = []
    tool_use_id = None
    content = rec.get("message", {}).get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tool_use_id = block.get("tool_use_id")
                c = block.get("content")
                if isinstance(c, str):
                    texts.append(c)
                elif isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "text":
                            texts.append(b.get("text", ""))
    persisted_bytes = None
    tur = rec.get("toolUseResult")
    if isinstance(tur, dict):
        p = tur.get("persistedOutputPath")
        if p and os.path.isfile(p):
            try:
                persisted_bytes = os.path.getsize(p)
            except OSError:
                persisted_bytes = None
    return "\n".join(texts), persisted_bytes, tool_use_id


def after_start(ts: str, start_utc: str) -> bool:
    return True if not start_utc else ts >= start_utc


def _median(values: List[float]) -> float:
    return statistics.median(values) if values else 0.0


def aggregate_group(project_dir: str, sessions: Optional[List[str]],
                    start_utc: str, tok: Tokenizer) -> Dict[str, Any]:
    key_dir = key_dir_for(project_dir)
    files = collect_jsonl(key_dir)
    tu_index = build_tool_use_index(files)
    sess_filter = set(sessions) if sessions else None

    tokens: Dict[str, Dict[str, int]] = {}   # sid -> {raw_read, index_read}
    chars: Dict[str, int] = {}
    usage: Dict[str, int] = {}
    quality: set = set()
    counted = 0
    persist = 0

    for path in files:
        for rec in iter_records(path):
            sid = rec.get("sessionId", "")
            if sess_filter is not None and sid not in sess_filter:
                continue
            if not after_start(rec.get("timestamp", ""), start_utc):
                continue
            rtype = rec.get("type")
            if rtype == "assistant":
                u = rec.get("message", {}).get("usage", {})
                if isinstance(u, dict):
                    usage[sid] = usage.get(sid, 0) + int(u.get("input_tokens", 0) or 0) \
                        + int(u.get("cache_creation_input_tokens", 0) or 0)
                content = rec.get("message", {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            quality.update(REQ_ID_RE.findall(block.get("text", "")))
            elif rtype == "user":
                text, persisted, tuid = result_text(rec)
                if not tuid or tuid not in tu_index:
                    continue
                tu = tu_index[tuid]
                cls = classify_target(tu["name"], tu["input"])
                if cls is None:
                    continue
                bucket = "index_read" if cls == "index" else "raw_read"
                tokens.setdefault(sid, {"raw_read": 0, "index_read": 0})
                n = tok.count(text)
                if n is not None:
                    tokens[sid][bucket] += n
                chars[sid] = chars.get(sid, 0) + len(text)
                counted += 1
                if persisted is not None:
                    persist += 1

    trials = sorted(set(list(tokens.keys()) + list(usage.keys())))
    primary = [tokens.get(s, {"raw_read": 0, "index_read": 0})["raw_read"]
               + tokens.get(s, {"raw_read": 0, "index_read": 0})["index_read"] for s in tokens]
    raw = [tokens[s]["raw_read"] for s in tokens]
    idx = [tokens[s]["index_read"] for s in tokens]
    return {
        "project_dir": project_dir,
        "trials": len(trials),
        "primary_indicator_median": _median(primary),
        "raw_read_median": _median(raw),
        "index_read_median": _median(idx),
        "secondary_noncached_input_median": _median([float(usage[s]) for s in usage]),
        "char_sum_median": _median([float(chars[s]) for s in chars]),
        "per_trial_primary": primary,
        "counted_sdd_tool_results": counted,
        "persisted_output_hits": persist,
        "_quality": quality,
    }


def summarize(per_group: Dict[str, Dict[str, Any]], tok: Tokenizer,
              compare: bool) -> Dict[str, Any]:
    delta: Dict[str, Any] = {}
    verdict = "inconclusive"
    reason = ""
    quality = {g: d.pop("_quality", set()) for g, d in per_group.items()}

    if not tok.available:
        reason = "no real tokenizer backend (set ANTHROPIC_API_KEY); token sums are 0, see char_sum_median"
    elif compare and "off" in per_group and "on" in per_group:
        off_m = per_group["off"]["primary_indicator_median"]
        on_m = per_group["on"]["primary_indicator_median"]
        reduction = off_m - on_m
        pct = (reduction / off_m * 100.0) if off_m else 0.0
        off_sec = per_group["off"]["secondary_noncached_input_median"]
        on_sec = per_group["on"]["secondary_noncached_input_median"]
        sec_ok = on_sec <= off_sec * 1.02
        q_off, q_on = quality.get("off", set()), quality.get("on", set())
        q_ok = q_off.issubset(q_on) if q_off else True
        if per_group["off"]["trials"] < 1 or per_group["on"]["trials"] < 1:
            verdict, reason = "inconclusive", "missing trials in one group"
        elif pct >= 30.0 and sec_ok and q_ok:
            verdict = "pass"
        elif reduction <= 0 or not sec_ok:
            verdict = "fail"
        else:
            verdict = "no_difference"
        delta = {
            "reduction_tokens": reduction, "reduction_pct": round(pct, 2),
            "secondary_non_worsening": sec_ok, "quality_equivalent": q_ok,
            "quality_missing_ids": sorted(q_off - q_on),
        }
    else:
        reason = "dry-run / single group; no off/on comparison"

    return {
        "tokenizer_backend": tok.backend_name,
        "groups": per_group,
        "delta": delta,
        "verdict": verdict,
        "verdict_reason": reason,
    }


def write_outputs(result: Dict[str, Any], out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    lines = ["# Issue #16 Step1 A/B Result (2-project)", ""]
    lines.append(f"- tokenizer backend: `{result['tokenizer_backend']}`")
    lines.append(f"- verdict: **{result['verdict']}**"
                 + (f" ({result['verdict_reason']})" if result["verdict_reason"] else ""))
    lines.append("")
    for g, d in result["groups"].items():
        lines.append(f"## group: {g}  ({d.get('project_dir', '')})")
        lines.append(f"- trials: {d['trials']}, counted .sdd tool_results: {d['counted_sdd_tool_results']}"
                     f" (persisted hits: {d['persisted_output_hits']})")
        lines.append(f"- primary indicator (.sdd tool_result tokens) median: {d['primary_indicator_median']}")
        lines.append(f"  - raw_read median: {d['raw_read_median']}, index_read median: {d['index_read_median']}")
        lines.append(f"- secondary (non-cached input) median: {d['secondary_noncached_input_median']}")
        lines.append(f"- char_sum median (sanity ref): {d['char_sum_median']}")
        lines.append("")
    if result["delta"]:
        d = result["delta"]
        lines.append("## delta (off - on)")
        lines.append(f"- reduction: {d.get('reduction_tokens')} tokens ({d.get('reduction_pct')}%)")
        lines.append(f"- secondary non-worsening: {d.get('secondary_non_worsening')}")
        lines.append(f"- quality equivalent: {d.get('quality_equivalent')} (missing ids: {d.get('quality_missing_ids')})")
        lines.append("")
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate A/B tokens (2-project).")
    parser.add_argument("--manifest", default="", help="run manifest.json (A/B mode)")
    parser.add_argument("--off-dir", default="", help="off group project dir (manifest-less A/B)")
    parser.add_argument("--on-dir", default="", help="on group project dir (manifest-less A/B)")
    parser.add_argument("--project-dir", default="", help="single dir dry-run (parser self-check)")
    parser.add_argument("--since", default="", help="start_utc filter for --off-dir/--on-dir/--project-dir")
    parser.add_argument("--out-dir", default="", help="output dir for result.json/summary.md")
    args = parser.parse_args()

    tok = Tokenizer()
    groups_spec: Dict[str, Tuple[str, Optional[List[str]]]] = {}
    start_utc = args.since
    compare = True

    if args.manifest and os.path.isfile(args.manifest):
        with open(args.manifest, encoding="utf-8") as f:
            m = json.load(f)
        start_utc = m.get("start_utc", "")
        groups_spec["off"] = (m["off"]["project_dir"], m["off"].get("sessions"))
        groups_spec["on"] = (m["on"]["project_dir"], m["on"].get("sessions"))
    elif args.off_dir and args.on_dir:
        groups_spec["off"] = (args.off_dir, None)
        groups_spec["on"] = (args.on_dir, None)
    elif args.project_dir:
        groups_spec["all"] = (args.project_dir, None)
        compare = False
    else:
        parser.error("provide --manifest, or --off-dir/--on-dir, or --project-dir")

    per_group = {g: aggregate_group(pd, sess, start_utc, tok)
                 for g, (pd, sess) in groups_spec.items()}
    result = summarize(per_group, tok, compare)

    if args.out_dir:
        write_outputs(result, args.out_dir)
    print(json.dumps({
        "tokenizer_backend": result["tokenizer_backend"],
        "verdict": result["verdict"],
        "verdict_reason": result["verdict_reason"],
        "groups": {g: {
            "trials": d["trials"],
            "counted_sdd_tool_results": d["counted_sdd_tool_results"],
            "primary_indicator_median": d["primary_indicator_median"],
            "char_sum_median": d["char_sum_median"],
        } for g, d in result["groups"].items()},
        "delta": result["delta"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
