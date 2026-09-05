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
2. **世代間比較の誤用チェック**: old/without と new/without を比較して差分を
   報告している箇所がないか（ASSERTION_DESIGN.md が明確に禁止している比較）。
   有効な比較は同一世代内（old/skill vs old/without、new/skill vs new/without）のみ
3. **grader の eval_feedback 集約**: 全 run 分の `grading.json` の
   `eval_feedback.suggestions` をスキルごとに集約し、複数 run で同じ指摘が出ている
   ものを優先度高として報告する
4. **評価インフラ自体のカバレッジ**: `.claude/skill-evals/<skill>/evals.json` が
   存在しないスキル（評価対象から漏れているスキル）の一覧と、存在するが eval 数が
   極端に少ない（1件のみ等）スキルを報告する

## 出力

`<report-dir>/meta_analysis.json` に以下の構造で保存する:

```json
{
  "skill_improvements": [
    {"skill": "...", "suggestions": ["..."], "source_runs": ["old/skill", "new/skill"]}
  ],
  "assertion_design_violations": [
    {"skill": "...", "assertion": "...", "issue": "..."}
  ],
  "non_discriminating_assertions": [
    {"skill": "...", "assertion": "...", "reason": "with/withoutの両方で常にpassしている"}
  ],
  "invalid_generation_comparisons": [
    {"skill": "...", "issue": "old/withoutとnew/withoutを直接比較している"}
  ],
  "coverage_gaps": {
    "missing_evals": ["skill-name", "..."],
    "thin_evals": [{"skill": "...", "eval_count": 1}]
  }
}
```
