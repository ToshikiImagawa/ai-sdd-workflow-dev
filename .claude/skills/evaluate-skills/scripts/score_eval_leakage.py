#!/usr/bin/env python3
"""eval prompt / fixture が SKILL.md の指示内容を漏洩している度合いの、決定的・LLM不使用な粗い代理指標。

SKILL.md 中の `inline code` スパン（フィールド名・パス・コマンド・フラグ等、素の熟練エンジニアが
SKILL.md を読まない限り知りようがない語彙の近似）を「特徴語」として抽出し、その特徴語が
(a) eval の prompt 本文、(b) 対応する fixture 配下の全ファイルに、そのままの形でどれだけ
出現するかを数える。

これは粗い一次フィルタに過ぎない。スコアが高いことは「漏洩している」ことを証明しないし
（ドメイン上不可避な共通語彙の可能性がある）、スコアが低いことも「漏洩していない」ことを
証明しない（構造的な漏洩は語彙一致では捉えられない）。実際の判定は Step 5 のメタ評価が
without_skill run の transcript.md と併せて行う。本スクリプトの役割は、LLM呼び出しゼロで
候補を安価に浮き上がらせることだけ。

Usage: score_eval_leakage.py <skill-evals-root> <plugin-skills-root> <fixtures-root> <output-path>
  skill-evals-root:   .claude/skill-evals            (each <skill>/evals.json)
  plugin-skills-root: plugins/sdd-workflow/skills     (each <skill>/SKILL.md)
  fixtures-root:      <report-dir>/fixtures           (each {old,new}/<skill>/...)
  output-path:        <report-dir>/eval_leakage_scores.json
"""
import json
import os
import re
import sys

CODE_SPAN_RE = re.compile(r"`([^`]+)`")


def distinctive_terms(skill_md_text):
    terms = set()
    for m in CODE_SPAN_RE.finditer(skill_md_text):
        t = m.group(1).strip()
        if len(t) >= 3 and not t.startswith("$"):
            terms.add(t.lower())
    return terms


def read_fixture_text(fixture_dir):
    if not os.path.isdir(fixture_dir):
        return ""
    chunks = []
    for root, _dirs, files in os.walk(fixture_dir):
        for fn in files:
            path = os.path.join(root, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    chunks.append(f.read())
            except OSError:
                continue
    return "\n".join(chunks)


def overlap_ratio(terms, haystack_lower):
    if not terms:
        return 0.0
    hit = sum(1 for t in terms if t in haystack_lower)
    return round(hit / len(terms), 4)


def main():
    if len(sys.argv) != 5:
        print(
            "usage: score_eval_leakage.py <skill-evals-root> <plugin-skills-root> "
            "<fixtures-root> <output-path>",
            file=sys.stderr,
        )
        sys.exit(1)

    skill_evals_root, plugin_skills_root, fixtures_root, output_path = sys.argv[1:5]
    scores = []

    for skill in sorted(os.listdir(skill_evals_root)):
        evals_path = os.path.join(skill_evals_root, skill, "evals.json")
        skill_md_path = os.path.join(plugin_skills_root, skill, "SKILL.md")
        if not (os.path.exists(evals_path) and os.path.exists(skill_md_path)):
            continue

        skill_md_text = open(skill_md_path, encoding="utf-8").read()
        terms = distinctive_terms(skill_md_text)
        evals = json.load(open(evals_path, encoding="utf-8")).get("evals", [])

        for ev in evals:
            prompt_lower = ev.get("prompt", "").lower()
            prompt_overlap = overlap_ratio(terms, prompt_lower)
            for era in ("old", "new"):
                fixture_dir = os.path.join(fixtures_root, era, skill)
                fixture_text_lower = read_fixture_text(fixture_dir).lower()
                fixture_overlap = overlap_ratio(terms, fixture_text_lower)
                scores.append({
                    "skill": skill,
                    "eval_id": ev.get("id"),
                    "era": era,
                    "distinctive_term_count": len(terms),
                    "prompt_overlap_ratio": prompt_overlap,
                    "fixture_overlap_ratio": fixture_overlap,
                    "combined_overlap_ratio": round(max(prompt_overlap, fixture_overlap), 4),
                })

    scores.sort(key=lambda s: -s["combined_overlap_ratio"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    top = [s for s in scores if s["combined_overlap_ratio"] >= 0.5]
    print(f"{len(scores)} score(s) written to {output_path}; {len(top)} candidate(s) with overlap >= 0.5")


if __name__ == "__main__":
    main()
