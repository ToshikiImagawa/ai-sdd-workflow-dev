# Analysis Guide（evaluate-skills 用）

メタ評価エージェントは、まず skill-creator プラグインの `agents/analyzer.md` の
「Analyzing Benchmark Results」セクション（パスは `scripts/resolve_skill_creator_path.sh` で
解決する）を読み込み、そこに書かれた観点（non-discriminating assertion、high-variance eval、
時間/トークンのトレードオフ等）を全スキル分の grading データに適用する。

## このプロジェクト特有の追加観点

1. **ASSERTION_DESIGN.md 遵守チェック**: 各スキルの `evals.json` の assertion が、
   `.claude/skill-evals/ASSERTION_DESIGN.md` が定める「バージョン中立」の基準に
   違反していないか（特定世代のファイルパス・フィールド名・語彙を assertion に
   埋め込んでいないか）を確認する
2. **世代間比較の誤用チェック**: `main_without` と `develop_without` を直接比較して差分を
   報告している箇所がないか、`main_skill` と `develop_skill` の生スコアを並べて優劣を語って
   いる箇所がないか（ASSERTION_DESIGN.md が明確に禁止している比較）。有効なのは同一世代内の
   リフト（`era_skill` vs `era_without`）と、その差 `lift(develop) − lift(main)` だけ。
   **リフトの差を取ることは禁止に当たらない** — 比較している量が生スコアではなくリフトなので、
   世代ごとのコーパスの違いは両辺の `without` に吸収される
3. **grader の eval_feedback 集約**: 全 run 分の `grading.json` の
   `eval_feedback.suggestions` をスキルごとに集約し、複数 run で同じ指摘が出ている
   ものを優先度高として報告する
4. **評価インフラ自体のカバレッジ**: `.claude/skill-evals/<skill>/evals.json` が
   存在しないスキル（評価対象から漏れているスキル）の一覧と、存在するが eval 数が
   極端に少ない（1件のみ等）スキルを報告する
5. **Vacuous Baseline の4仮説分類（最重要）**: `<report-dir>/vacuous_baseline_candidates.json`
   （`scripts/detect_vacuous_baselines.py` の出力。Step 4 で生成済み）の各候補を
   `references/vacuous-baseline-diagnostic.md` が定める4仮説（`skill_unnecessary` /
   `weak_assertions` / `cost_inefficiency` / `prompt_leakage`）で分類する。判定には以下を
   すべて突き合わせる:
   - 対応する `without_skill` run の `grading.json` の `eval_feedback.overall`（grading-guide.md
     の指示により一次仮説が既に書かれているはず）
   - `<report-dir>/eval_leakage_scores.json`（`scripts/score_eval_leakage.py` の出力。
     Step 2 で生成済み）の該当 (skill, era) の overlap ratio — 高い場合は `prompt_leakage` の
     裏付け候補。ただし overlap が高いだけで自動的に `prompt_leakage` と断定しない
     （ドメイン上不可避な共通語彙の可能性を transcript.md で確認すること）
   - `metrics.json` 由来の `total_tool_calls`/`output_chars` の with/without 差 — with_skill 側が
     目安1.5倍以上多いにもかかわらず lift が 0 以下なら `cost_inefficiency` の裏付け
   - `without_skill` run の transcript.md が SKILL.md を読まずに正解相当の判断に到達していれば
     `skill_unnecessary` の裏付け
   単一仮説に決め切れない場合は複数の `likely_cause` と `confidence` を併記してよい。
   **`recommended_action` は提示のみ。`evals.json`/`SKILL.md`/fixture を自動的に書き換えない**
   （`references/vacuous-baseline-diagnostic.md` の非対象事項を参照）
6. **継続未対応チェック**: `<report-dir>/recurring_findings_candidates.json`
   （`scripts/diff_recurring_findings.py` の出力。完全一致のみを検出）を読み、まず
   そのまま `recurring_unaddressed_findings` の候補として採用する。加えて、完全一致では
   拾えない「言い回しが変わった同種の指摘」（例: assertion文言が書き換えられたが弱さの本質は
   変わっていないケース）を、今回の `non_discriminating_assertions` と過去レポートの内容を
   読み比べて LLM 判断で追加検出する
7. **evaluate-skills 自身の自己反省**: `scripts/audit_run_artifacts.py` の出力
   `<report-dir>/run_artifact_audit.json` を読む。これは対象10スキルの評価データではなく
   **evaluate-skills 自身**（このSKILL.mdとscriptsが生成した runs/ 配下のアーティファクト）の
   健全性を機械集計したものである:
   - `counts` の `metrics_present`/`timing_present` が `total_runs` に対して低ければ、
     Step 3 の executor プロンプトの指示が実効的に守られていないことを示す
   - `misplaced_grading_json` が空でなければ、grader が保存先パスを誤解している
     （grading-guide.md の記述が曖昧である可能性がある）
   - `safety_guard_keyword_hits` は「実際に迂回・回避を行った」ことを示す事後表現の
     候補に過ぎない（否定文脈は機械的に除外済みだが、それでも確定した違反ではない）。
     **各候補について、該当 run の transcript.md/user_notes.md を実際に読んで
     本当に安全ガード違反が起きたのかを確認すること。読まずに件数だけで判断しない**
   これらを `meta_analysis.json` の `evaluate_skills_self_review` フィールドにまとめる。
   **改善提案は提示のみ。evaluate-skills 自身の SKILL.md/scripts を自動的に書き換えない**
   （対象スキルの evals.json を書き換えない、という既存の非侵襲方針と同じ扱い）。

## 出力

`<report-dir>/meta_analysis.json` に以下の構造で保存する（`skill_improvements` から
`coverage_gaps` までの5フィールドは既存どおり維持し、`vacuous_baselines`・
`recurring_unaddressed_findings`・`evaluate_skills_self_review` を追加する）:

```json
{
  "skill_improvements": [
    {"skill": "...", "suggestions": ["..."], "source_runs": ["main_skill", "develop_skill"]}
  ],
  "assertion_design_violations": [
    {"skill": "...", "assertion": "...", "issue": "..."}
  ],
  "non_discriminating_assertions": [
    {"skill": "...", "assertion": "...", "reason": "with/withoutの両方で常にpassしている"}
  ],
  "invalid_generation_comparisons": [
    {"skill": "...", "issue": "main_without と develop_without を直接比較している"}
  ],
  "coverage_gaps": {
    "missing_evals": ["skill-name", "..."],
    "thin_evals": [{"skill": "...", "eval_count": 1}]
  },
  "vacuous_baselines": [
    {
      "skill": "...",
      "era": "old|new",
      "without_pass_rate": 1.0,
      "skill_pass_rate": 1.0,
      "likely_cause": "skill_unnecessary|weak_assertions|cost_inefficiency|prompt_leakage|undetermined",
      "confidence": "high|medium|low",
      "evidence": "...",
      "recommended_action": "..."
    }
  ],
  "recurring_unaddressed_findings": [
    {
      "finding": "...",
      "skill": "...",
      "seen_in_reports": ["2026-09-06", "2026-09-07"],
      "times_seen": 3,
      "still_unresolved": true
    }
  ],
  "evaluate_skills_self_review": {
    "artifact_capture_health": {
      "metrics_json_present": "38/40",
      "timing_json_present": "40/40",
      "grading_json_malformed": 0,
      "misplaced_grading_json": 0
    },
    "confirmed_safety_guard_incidents": [
      {"skill": "...", "condition": "...", "description": "transcript.md/user_notes.mdを実際に読んで確認した内容"}
    ],
    "suggested_improvements": ["SKILL.md/scripts への具体的な改善提案（提示のみ）"]
  }
}
```
