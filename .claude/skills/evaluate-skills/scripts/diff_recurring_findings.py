#!/usr/bin/env python3
"""過去のレポートと比較し、同じ assertion の弱さが何度再発しているかを検出する。

「診断はできるが治療されない」ループ（同じ assertion の弱さが複数回のフルスイート評価で
繰り返し指摘されるが evals.json が更新されない）を可視化するための決定的チェック。

この報告(current-report-dir)の meta_analysis.json はまだ存在しない時点（Step 5 の直前）で
実行するため、current 側は grading.json の `expectations[]` から「with_skill/without_skill
両方で passed=true」という機械的な代理指標で non-discriminating 候補を作る（LLM判断は使わない）。
過去のレポート側は、そのレポート自身の meta_analysis.json（すでにLLMが精査済みの
`non_discriminating_assertions`）をそのまま使う。current 側の機械的候補が、過去いずれかの
LLM精査済みリストに (skill, assertion文字列) 完全一致で存在すれば「再発」とみなす。

言い回しが変わった同種の指摘（reworded duplicate）はここでは検出できない。Step 5 の
メタ評価エージェントが本スクリプトの出力を seed として、LLM判断で追加のreworded重複を
拾うことを想定している。

Usage: diff_recurring_findings.py <reports-root> <current-report-dir>
Writes: <current-report-dir>/recurring_findings_candidates.json
"""
import json
import os
import sys


def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def current_mechanical_candidates(current_report_dir):
    """grading.json の expectations[] から、with/without 両方で passed=true な
    (skill, assertion文字列) を機械的に列挙する。"""
    runs_root = os.path.join(current_report_dir, "runs")
    candidates = {}
    if not os.path.isdir(runs_root):
        return candidates

    for skill in sorted(os.listdir(runs_root)):
        skill_dir = os.path.join(runs_root, skill)
        if not os.path.isdir(skill_dir):
            continue
        for eval_id in sorted(os.listdir(skill_dir)):
            eval_dir = os.path.join(skill_dir, eval_id)
            if not os.path.isdir(eval_dir):
                continue
            subdirs = {d for d in os.listdir(eval_dir) if os.path.isdir(os.path.join(eval_dir, d))}
            eras = sorted(
                d[: -len("_without")]
                for d in subdirs
                if d.endswith("_without") and f"{d[: -len('_without')]}_skill" in subdirs
            )
            for era in eras:
                wo = load_json(os.path.join(eval_dir, f"{era}_without", "grading.json"))
                sk = load_json(os.path.join(eval_dir, f"{era}_skill", "grading.json"))
                if not wo or not sk:
                    continue
                wo_passed = {
                    e.get("text") for e in wo.get("expectations", []) if e.get("passed")
                }
                sk_passed = {
                    e.get("text") for e in sk.get("expectations", []) if e.get("passed")
                }
                for text in wo_passed & sk_passed:
                    if text:
                        candidates[(skill, text)] = True
    return candidates


def past_non_discriminating_map(reports_root, previous_reports):
    """(skill, assertion) -> 出現したレポート名リスト。過去レポートの meta_analysis.json
    (LLM精査済み) の non_discriminating_assertions をそのまま使う。"""
    seen = {}
    for rd in previous_reports:
        meta = load_json(os.path.join(reports_root, rd, "meta_analysis.json"))
        if not meta:
            continue
        for item in meta.get("non_discriminating_assertions", []):
            key = (item.get("skill"), item.get("assertion"))
            seen.setdefault(key, []).append(rd)
    return seen


def main():
    if len(sys.argv) != 3:
        print("usage: diff_recurring_findings.py <reports-root> <current-report-dir>", file=sys.stderr)
        sys.exit(1)

    reports_root, current_report_dir = sys.argv[1], sys.argv[2]
    current_name = os.path.basename(os.path.normpath(current_report_dir))

    all_reports = sorted(
        d for d in os.listdir(reports_root)
        if os.path.isdir(os.path.join(reports_root, d))
    )
    # 日付+サフィックス（"2026-09-08" < "2026-09-08-v2" < "2026-09-08-v3"）は文字列比較で
    # 正しく順序が成立する。current より前のものだけを「過去のレポート」として扱う。
    previous_reports = [d for d in all_reports if d < current_name]

    current_candidates = current_mechanical_candidates(current_report_dir)
    past_map = past_non_discriminating_map(reports_root, previous_reports)

    results = []
    for key in current_candidates:
        seen_in = past_map.get(key, [])
        if seen_in:
            skill, assertion = key
            results.append({
                "skill": skill,
                "assertion": assertion,
                "seen_in_reports": seen_in,
                "times_seen": len(seen_in) + 1,
            })

    results.sort(key=lambda c: -c["times_seen"])

    out_path = os.path.join(current_report_dir, "recurring_findings_candidates.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"{len(results)} recurring candidate(s) written to {out_path}")


if __name__ == "__main__":
    main()
