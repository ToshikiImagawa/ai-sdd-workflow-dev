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
- **世代（main / develop）をまたいで採点内容を比較しない。** `main` のフィクスチャ上で
  実行した run は、`main` 世代の CONSTITUTION.md・AI-SDD-PRINCIPLES.md・SKILL.md の世界の中で
  のみ評価する。`develop` 世代の語彙やファイル配置（`adr/`、`design-draft.md` 等）と比較して
  「古い」「対応していない」と減点してはならない。フィクスチャは各ブランチの実 `.sdd/` ツリー
  なので、世代ごとの規則書はそれぞれ正しい
  （判定基準の正典は `.claude/skill-evals/ASSERTION_DESIGN.md`）
- Step 6「Critique the Evals」で得られる `eval_feedback` は必ず出力させる。空でも
  `"overall": "No suggestions, evals look solid"` のように明示する。これが
  評価手法自体のメタ評価（`references/analysis-guide.md`）の主要な入力になる
- **`without_skill` の run で `summary.pass_rate` が 1.0 になった場合**、`eval_feedback.overall`
  の末尾に、この run 単独で判断できる範囲で一次仮説を一文添える:
  「`skill_unnecessary`（この課題は本質的にSDD固有知識を要さない）か `weak_assertions`
  （assertionが形式的で本質を捉えていない）のどちらに近いか、あるいは対応する `_skill` run との
  比較が必要か」（判定基準は `references/vacuous-baseline-diagnostic.md`）。
  **これは既存の `eval_feedback.overall` という自由記述フィールドの中に文章として書き込む。
  `grading.json` に新しいトップレベルキーを追加してはならない**
  （`grading.json`/`benchmark.json` のフィールド名は skill-creator の `references/schemas.md`
  が定める正典であり、未知のキーを追加すると viewer との対応関係が不明瞭になる。新しい
  構造化データは `meta_analysis.json` 側に置く）
- executor が `{outputs_dir}/metrics.json` を書いていない場合、grader.md Step 8 に従い
  transcript.md からの手動集計を試みる。それでも算出不可能な場合は `execution_metrics` に
  `{"note": "metrics.json が存在せず、transcript.md からの手動集計でも算出不可"}` と明記する
  （省略せず、算出不可であることを明示的に記録する）
