# HTML Report Guide（evaluate-skills 用）

## Step 1: ベースHTMLの生成

skill-creator の `eval-viewer/generate_review.py --static` で、Outputs/Benchmark タブを
持つスタンドアロン HTML を生成する（コマンド例は SKILL.md の Step 6 を参照）。
JS/CSS を含む viewer 本体は手を加えない — 既存タブの挙動（アウトプット閲覧・
ベンチマーク集計表示）を壊さないため。

## Step 2: 追加セクションの注入

生成された `<report-dir>/report.html` の `</body>` 直前に、以下2セクションを
文字列置換で挿入する（Python の `str.replace("</body>", ..., 1)` で十分。
DOM パーサは不要）。データソースは `<report-dir>/meta_analysis.json`。

### セクション1: スキル改善提案（`skill_improvements`）

スキルごとに `<h3>` + `<ul>` で提案を列挙する。どの run（old/skill・new/skill）から
得られた指摘かを併記する。

### セクション2: 評価手法自体の改善点

以下4項目をそれぞれ `<h3>` で見出しを立てて列挙する:

1. ASSERTION_DESIGN.md 遵守違反（`assertion_design_violations`）
2. 判別力のない assertion（`non_discriminating_assertions`）
3. 世代間比較の誤用（`invalid_generation_comparisons`）
4. 評価カバレッジの欠落（`coverage_gaps`）

## 注意

- 挿入する HTML はインラインスタイルのみで完結させる（viewer 本体の CSS クラス名と
  衝突しないよう、`class` 属性は使わず `style` 属性で装飾する）
- 各セクションの先頭に生成日時と対象スキル数を明記し、レポートだけを見て
  「いつ・何を対象に評価したか」が分かるようにする
