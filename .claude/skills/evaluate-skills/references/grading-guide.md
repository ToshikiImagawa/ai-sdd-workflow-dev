# Grading Guide（evaluate-skills 用）

独立グレーダーサブエージェントを起動する際は、まず skill-creator プラグインの
`agents/grader.md`（パスは `scripts/resolve_skill_creator_path.sh` で解決する）を読み込ませ、
そこに書かれた Process（Step 1〜8）と Output Format をそのまま採点の基準として使う。

## このプロジェクト特有の差分

- `.claude/skill-evals/<skill>/evals.json` の `assertions[].text` を、grader.md の
  `expectations` として渡す。`checked_by` フィールドは常に固定値
  （`"independent grader (reads the run transcript and the produced files)"`）で
  意味を持たないため無視してよい
- `grading.json` の保存先は `<report-dir>/runs/<skill>/<eval-id>/<condition>/grading.json`
  とする（grader.md 本来の既定 `{outputs_dir}/../grading.json` と同じ相対関係）
- **世代（old/new）をまたいで採点内容を比較しない。** old fixture 上で実行した run は
  old 世代の CONSTITUTION.md・SKILL.md の世界の中でのみ評価する。new 世代の語彙や
  ファイル配置と比較して「古い」「対応していない」と減点してはならない
  （判定基準の正典は `.claude/skill-evals/ASSERTION_DESIGN.md`）
- Step 6「Critique the Evals」で得られる `eval_feedback` は必ず出力させる。空でも
  `"overall": "No suggestions, evals look solid"` のように明示する。これが
  評価手法自体のメタ評価（`references/analysis-guide.md`）の主要な入力になる
