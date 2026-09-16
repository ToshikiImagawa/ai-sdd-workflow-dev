---
id: "adr-document-model-migration"
title: "ドキュメントモデル移行（v4.x design.md -> v5 adr/） 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-09-16"
updated: "2026-09-16"
sdd-version: "5.0.0"
depends-on: []
tags: ["migration", "adr", "sdd-v5"]
category: "document-model-migration"
---

# ドキュメントモデル移行（v4.x design.md -> v5 adr/） 決定ログ

## 2026-09-16 各design docの「9. 設計判断」節のみをADRエントリへ抽出する

- **Decision**: `specification/*_design.md` から ADR へ移行する際、「9. 設計判断」節（決定事項・選択肢・
  却下理由）のみを抽出し、実装ステータス・アーキテクチャ・データ構造・ファイル構成・テスト戦略・
  未解決の課題は移行しない。
- **Rationale**: `ADR_TEMPLATE.md` §「ここに書かないもの」が、技術設計の全体プランや「何をするか」の
  抽象的記述を ADR の対象外と定めているため。ADR は「なぜその決定をしたか」の記録に限定する。
- **Rejected alternatives**: design doc 全文を ADR へ転記する — ADR が実装詳細で肥大化し、決定の追跡性が
  下がるため却下。

## 2026-09-16 パイロット1件で形式を確定してから残り23件を処理する

- **Decision**: 24件のうち `distribution.md` をパイロットとして先に ADR 化し、フィールド名
  （`- **Decision**:` / `- **Rationale**:` / `- **Rejected alternatives**:` の英語表記）と抽出範囲の
  解釈が妥当かを確認したうえで、残り23件を同一方式で処理した。
- **Rationale**: 24件を一括生成してから形式の誤りに気づくと、全件をやり直すことになる。1件で解釈のずれを
  検出すれば手戻りを最小化できる。
- **Rejected alternatives**: 24件を並行して一括生成する — 形式の解釈ずれがあった場合の手戻りコストが
  高いため却下。

## 2026-09-16 移行完了後に元のdesign docを削除し、spec側のリンクをADRへ張り替える

- **Decision**: 決定の移行が完了した `specification/*_design.md` は削除し、対応する `*_spec.md` の
  「関連 Design Doc」リンクを「関連 ADR」へ張り替える。
- **Rationale**: 決定が ADR に append-only で保存された後は、元の design doc を残すと同じ決定の記録が
  2箇所に分裂し、どちらが真実の源か不明瞭になる。`MIGRATION_PENDING.md` は該当ファイルの存在を検知して
  自動生成されるため、削除しない限り消滅しない。
- **Rejected alternatives**: design doc をそのまま残し ADR だけ追加する（並存） — 情報源が分裂し
  `MIGRATION_PENDING.md` も消滅しないため却下。

## 2026-09-16 PRD本文中の`*_design.md`という概念言及は書き換えず据え置く

- **Decision**: `.sdd/requirement/quality-guardrails/doc-consistency-check.md` の2箇所（22行目・92行目）
  にある `*_design.md` への言及（リンクではなく PRD 本文の説明文）は、本移行では書き換えず据え置く。
- **Rationale**: PRD（`.sdd/requirement/**`）は AI が独断で変更しない（PRD Non-Automation 原則）。
  `AskUserQuestion` で人間に判断を仰いだ結果、「据え置く」が選ばれた（issue #134 の PR で記録）。
- **Rejected alternatives**: 移行対象のリンク書き換えと同様に自動で書き換える — PRD Non-Automation
  原則に抵触するため却下。
