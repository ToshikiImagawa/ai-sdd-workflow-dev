#!/usr/bin/env python3
"""without_skill が with_skill を追い抜くか同点になる (skill, era) 組を機械的に列挙する。

benchmark.json ではなく runs/<skill>/<eval_id>/<era>_<variant>/grading.json を直接読む。
benchmark.json の eval_name はスキルをまたいで衝突しうる（例: finalize-prd と generate-prd が
どちらも "notification-badge-amend" という eval_name を使うケースが実際に発生した）ため、
skill/era の対応はディレクトリ構造から取るほうが安全。

Usage: detect_vacuous_baselines.py <report-dir>
Writes: <report-dir>/vacuous_baseline_candidates.json
"""
import json
import os
import sys


def main():
    if len(sys.argv) != 2:
        print("usage: detect_vacuous_baselines.py <report-dir>", file=sys.stderr)
        sys.exit(1)

    report_dir = sys.argv[1]
    runs_root = os.path.join(report_dir, "runs")
    candidates = []

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
                without_dir = os.path.join(eval_dir, f"{era}_without")
                skill_run_dir = os.path.join(eval_dir, f"{era}_skill")
                wo_path = os.path.join(without_dir, "grading.json")
                sk_path = os.path.join(skill_run_dir, "grading.json")
                if not (os.path.exists(wo_path) and os.path.exists(sk_path)):
                    continue

                try:
                    wo_rate = json.load(open(wo_path, encoding="utf-8")).get("summary", {}).get("pass_rate")
                except (json.JSONDecodeError, OSError) as e:
                    candidates.append({
                        "skill": skill, "era": era, "eval_id": eval_id,
                        "error": f"{wo_path} の読み込み失敗: {e}",
                    })
                    continue
                try:
                    sk_rate = json.load(open(sk_path, encoding="utf-8")).get("summary", {}).get("pass_rate")
                except (json.JSONDecodeError, OSError) as e:
                    candidates.append({
                        "skill": skill, "era": era, "eval_id": eval_id,
                        "error": f"{sk_path} の読み込み失敗: {e}",
                    })
                    continue

                if wo_rate is None or sk_rate is None:
                    continue

                if wo_rate >= sk_rate:
                    severity = (
                        "zero_lift_full_pass"
                        if wo_rate >= 0.999 and sk_rate >= 0.999
                        else "negative_or_zero_lift"
                    )
                    candidates.append({
                        "skill": skill,
                        "era": era,
                        "eval_id": eval_id,
                        "without_pass_rate": wo_rate,
                        "skill_pass_rate": sk_rate,
                        "lift": round(sk_rate - wo_rate, 4),
                        "severity": severity,
                        "without_run_dir": without_dir,
                        "skill_run_dir": skill_run_dir,
                    })

    out_path = os.path.join(report_dir, "vacuous_baseline_candidates.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"{len(candidates)} candidate(s) written to {out_path}")


if __name__ == "__main__":
    main()
