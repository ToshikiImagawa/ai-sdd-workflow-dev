# 既知の不安定ケース

`--runs 1` では出力の揺れで赤になることがあるケース。同じ grader が落ちた場合は「既知の揺れ」として報告し、
再実行で緑になるかを確認する。別の grader が落ちた場合は既知扱いにしない。

ケースを直した・実装を直して安定した場合はこの表から外す。新たに揺れが分かったら追記する（最終更新 2026-10-23）。

| ケース | 落ちる grader | 揺れの内容 | 根本側の候補 |
|:--|:--|:--|:--|
| `front-matter-validation/impl-status-reality-is-info` | `impl_status_reality_is_info` | エージェントが `impl-status` に言及しない回がある | spec 行 17 に対するエージェント定義の記述が薄い |
| `front-matter-validation/status-propagation-is-info` | `status_propagation_is_info` | 上流 PRD の `updated` が下流より新しい fixture でも status 伝播を報告しない回がある | 同上（行 18） |
| `vibe-detection/risk-level-exactly-one` | `risk_level_exactly_one` | スキルは起動しレベルも 1 つ出すが、ラベル行の形が毎回違う（`### Risk Level: High` / `**リスクレベル: High**` / 文中） | テンプレートをプレースホルダ化済み。改善傾向 |

実測の経緯（全件 18/32 → 27/32、部分再実行 21/23）は `.sdd/task/227/skill-evals-investigation.md` の「全件実行」節。
