# Vacuous Baseline 診断（4仮説の正典）

## これは何か

`without_skill.pass_rate >= with_skill.pass_rate` となる (skill, era) 組（特に
`without_skill` が 1.0 に達しているもの）を「スキルの有効性を測れていない run」として
機械的に列挙し、4つの仮説のいずれか（複数可）に分類するための正典。

2026-09-08 時点で過去5回のフルスイート評価（`.claude/skill-evals/reports/2026-09-06/`,
`2026-09-07/`, `2026-09-08/`, `2026-09-08-v2/`, `2026-09-08-v3/`）を横断集計した結果、
全77組の (skill, era) ペアのうち **48組（62.3%）で without_skill が pass_rate 100%**、
**60組（77.9%）で without_skill >= with_skill** だった。しかも5回すべての実行で
meta-analysis が non-discriminating な assertion を検出していた（3〜10件/回）にもかかわらず、
同じ問題が再発し続けていた。「診断はできるが治療されない」状態を放置すると、フルスイート評価は
毎回同じ結論を高コストで再生産するだけの儀式になる。本ドキュメントは、この診断を
Step 5 のメタ評価に組み込み、次に何をすべきかまで（提示のみ・実行はしない）明確にするための
判定基準を定める。

## 4仮説と判定基準

| 仮説 | 定義 | 判定に必要な証拠 | recommended_action（**提示のみ**。本skillは実行しない） |
|:---|:---|:---|:---|
| `skill_unnecessary` | 課題そのものが本質的にSDD固有知識・手順を要さず、熟練エンジニアなら誰でも同じ結論に達する | `without_skill` run の transcript.md が SKILL.md を読まずに正解相当の判断（トレーサビリティ維持・非破壊追記・実コード確認等）に到達している。grader の `eval_feedback.overall` が同種の一次仮説を述べている | このスキルの当該観点への適用を見直す（対象タスクの範囲を狭める、または他スキルへの統合・退役を検討） |
| `weak_assertions` | assertion が形式的・構造的なチェックに留まり、SDD固有の価値（トレーサビリティの実質、矛盾の検出、創作の排除等）を捉えていない | `grading.json` の `eval_feedback.suggestions` に該当する指摘がある。同一 assertion が複数レポートに渡って `non_discriminating_assertions` として繰り返し検出されている（`recurring_unaddressed_findings` 参照） | `.claude/skill-evals/ASSERTION_DESIGN.md` の判定基準に沿って assertion を書き換える（本skillは実施しない） |
| `cost_inefficiency` | 品質（pass_rate）が同等かそれ以下にもかかわらず、skill使用時のコスト（tool_calls・output_chars・wall-clock時間）が不釣り合いに悪化している | `metrics.json` 由来の `total_tool_calls`/`output_chars` が with_skill 側で目安1.5倍以上多い。または `timing.json` の `duration_seconds` が有意に長い | コスト差を数値で明示し、スキルの投資対効果の再検討を人間に促す（本skillは実施しない） |
| `prompt_leakage` | eval の prompt、またはそれに付随する fixture（CONSTITUTION.md・既存文書の実例等）が、SKILL.md の指示内容・語彙・手順をすでにほぼ完全に代替してしまっている | `scripts/score_eval_leakage.py` が出す overlap ratio が高い。かつ `without_skill` run が SKILL.md 固有の語彙・手順を自力で（読まずに）再現している | eval prompt または fixture の該当箇所を特定し、漏洩している具体的な情報（例: 既存文書に埋め込まれた完全な命名規則の実例）を薄める方向で書き換える（本skillは実施しない） |

単一仮説に決め切れない場合は、複数の `likely_cause` と各々の `confidence`（high/medium/low）を
併記してよい。証拠が乏しい場合は `likely_cause: "undetermined"` として、追加調査が必要な旨を
`evidence` に明記する。

## 既存の非公式判断との整合（校正用の実例）

この4仮説は、`.claude/skill-evals/ASSERTION_DESIGN.md` が個別スキルごとにすでに非公式に
下していた判断の一般化に過ぎない。新しい判断はこれらと矛盾しないこと。

- **`generate-prd` assertion 6（2026-09-08追記）**: 旧5件が pass_rate=1.0 で全条件タイになっていた
  ケース。実質は `weak_assertions`（矛盾検出という重要な観点を誰も検証していなかった）
- **`task-breakdown` assertion 6（2026-09-07追記）**: 同様に旧5件全タイ。front matter 規約準拠という
  「その世代固有のパターンを読んだか」を測る assertion が無かった、実質 `weak_assertions`
- **`implement` assertion群強化（2026-09-08）**: tool_calls が最大3.4倍に増えるにもかかわらず
  品質差が測れていなかったケース。実質 `cost_inefficiency` + `weak_assertions` の複合

## 非対象事項（重要）

本ドキュメントおよび Step 5 の出力（`vacuous_baselines` フィールド）は
**recommended_action の提示のみを行う**。`.claude/skill-evals/<skill>/evals.json`、対象スキルの
`SKILL.md`、fixture を自動的に書き換えることは evaluate-skills 自身の責務ではない
（Step 0 の「evals.json を今その場で書き起こすことはしない」という既存の非侵襲方針と同様）。
