# HTML Report Guide（evaluate-skills 用）

## Step 1: ベースHTMLの生成

skill-creator の `eval-viewer/generate_review.py --static` で、Outputs/Benchmark タブを
持つスタンドアロン HTML を生成する（コマンド例は SKILL.md の Step 6 を参照）。
JS/CSS を含む viewer 本体は手を加えない — 既存タブの挙動（アウトプット閲覧・
ベンチマーク集計表示）を壊さないため。

## Step 2: 追加セクションの注入

生成された `<report-dir>/report.html` の `</body>` 直前に、以下3セクションを
**この順番で**文字列置換で挿入する（Python の `str.replace("</body>", ..., 1)` で十分。
DOM パーサは不要）。データソースは `<report-dir>/meta_analysis.json`。

### セクション0（最優先・最上部）: ベースライン(skill無し)満点診断（`vacuous_baselines`）

**このセクションを他の2セクションより前に置く。** `without_skill` が `with_skill` と
同点または上回っている (skill, era) 組は、フルスイート評価が計測できていない最も重要な
問題であり、後回しにしてよい話題ではない（`references/vacuous-baseline-diagnostic.md` 参照）。

`skill` + `era` ごとに1行のテーブル行として、`without_pass_rate` / `skill_pass_rate` /
`likely_cause`（4仮説のいずれか。日本語ラベルに変換して表示: `skill_unnecessary`→
「スキル自体が不要」、`weak_assertions`→「assertionが本質を捉えていない」、
`cost_inefficiency`→「コスト悪化」、`prompt_leakage`→「promptの漏洩」）/ `confidence` /
`recommended_action` を表示する。`severity: "zero_lift_full_pass"`（両条件とも1.0）の行は
背景色を強調（例: 薄い黄〜橙）して視覚的に目立たせる。空配列の場合は
「今回は vacuous baseline に該当する組はありませんでした」と明示する。

### セクション1: スキル改善提案（`skill_improvements`）

スキルごとに `<h3>` + `<ul>` で提案を列挙する。どの run（`main_skill` / `develop_skill`）から
得られた指摘かを併記する。

### セクション2: 評価手法自体の改善点

以下4項目をそれぞれ `<h3>` で見出しを立てて列挙する:

1. ASSERTION_DESIGN.md 遵守違反（`assertion_design_violations`）
2. 判別力のない assertion（`non_discriminating_assertions`）
3. 世代間比較の誤用（`invalid_generation_comparisons`）
4. 評価カバレッジの欠落（`coverage_gaps`）

セクション末尾に5項目目として「継続未対応の指摘」（`recurring_unaddressed_findings`）を
追加する。`times_seen >= 3` の行は「N回連続で指摘されているが未対応」という文言を添えて
強調表示する（`recurring_unaddressed_findings` は「診断はできるが治療されない」ループの
可視化が目的であり、これ自体は指摘を強制的に解決しない点も一言添える）。

### セクション3: evaluate-skills 自身の実行品質（`evaluate_skills_self_review`）

対象10スキルの評価結果とは明確に区別して表示する（見出しに「evaluate-skills 自身について」
と明記し、対象スキルの改善提案と混同されないようにする）。`artifact_capture_health` は
表形式（`metrics_json_present`/`timing_json_present`/`grading_json_malformed`/
`misplaced_grading_json`）で表示し、`confirmed_safety_guard_incidents` が空でない場合は
警告色で強調する（人間がグレーダーを疑うより先に安全性の懸念に気付けるようにする）。
`suggested_improvements` は `<ul>` で列挙する。

## 注意

- 挿入する HTML はインラインスタイルのみで完結させる（viewer 本体の CSS クラス名と
  衝突しないよう、`class` 属性は使わず `style` 属性で装飾する）
- 各セクションの先頭に生成日時と対象スキル数を明記し、レポートだけを見て
  「いつ・何を対象に評価したか」が分かるようにする
