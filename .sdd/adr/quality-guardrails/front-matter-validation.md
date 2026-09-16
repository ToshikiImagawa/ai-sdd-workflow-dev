---
id: "adr-quality-guardrails-front-matter-validation"
title: "front matter 検証 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-08"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-quality-guardrails-front-matter-validation"]
tags: ["front-matter", "validation", "consistency-check"]
category: "quality-guardrails"
---

# front matter 検証 決定ログ

## 2026-07-08 front matter 検証をレビューエージェントとして実装する

- **Decision**: front matter 検証を skill やフックスクリプトではなく、レビューエージェント（agent）として実装する。
- **Rationale**: 生成と検証の責務を分離するため。検証はレビューとして生成スキルから独立して起動できる形が適切である。
- **Rejected alternatives**: 生成スキル内で検証する — 生成と検証の責務が混ざるため却下。hook スクリプトで実装する — 生成スキルから独立して起動する形にならないため却下。

## 2026-07-08 検証エージェントのモデルを haiku にする

- **Decision**: front-matter-reviewer のモデルを `haiku` とする。
- **Rationale**: ルール基盤の形式検証は複雑な推論を要さず、低コスト・低レイテンシで十分な精度が得られる（spec NFR-001 / DC_003）。
- **Rejected alternatives**: sonnet / opus — 形式検証に対して過剰なコストとレイテンシになるため却下。

## 2026-07-08 ツール権限を読み取り専用にする

- **Decision**: 検証エージェントのツールを読み取り系（+ AskUserQuestion）に限定する。
- **Rationale**: 検出専任であり自動修正しないという責務を構造的に保証するため。
- **Rejected alternatives**: 読み書き可にする — 検出専任の責務を構造的に保証できないため却下。

## 2026-07-08 横断チェックを `--cross-ref` オプションにする

- **Decision**: ID 一意性・依存整合性の横断チェックを常時実行せず、`--cross-ref` オプションで有効化する。
- **Rationale**: 横断チェックは全文書走査が必要でコストが高く、既定は高速な単一文書検証に留めるべきである（spec NFR-004）。
- **Rejected alternatives**: 常時実行する — 既定の検証が高コストになるため却下。

## 2026-07-08 Task による再帰探索を使わない

- **Decision**: 検証エージェント内で Task を使わず、Read / Glob / Grep で完結させる。
- **Rationale**: 再帰探索によるコンテキスト爆発を回避し、コンテキスト効率を優先する。
- **Rejected alternatives**: Task で再帰探索する — コンテキスト爆発を招くため却下。

## 2026-07-08 front matter の欠落を違反とせず info として扱う

- **Decision**: front matter が存在しない文書を error とせず info で報告する。
- **Rationale**: front matter はオプション（後方互換）であり、付与推奨を案内するのが適切である。
- **Rejected alternatives**: error として報告する — 後方互換の既存文書を違反扱いすることになるため却下。

## 2026-09-02 `sdd-version` 不在を info として扱う

- **Decision**: `sdd-version` フィールドの不在を error / warning とせず info で報告する。
- **Rationale**: 既存の欠落 front matter ポリシーと同じ扱いが一貫する。加えて `recommend-front-matter` が `sdd-version` を意図的に後付けしないため、不在は「フィールド導入前の文書」だけでなく「後付け対象外」を含む正常な状態である。
- **Rejected alternatives**: error / warning として報告する — 正常な状態を違反として報告することになるため却下。

## 2026-09-02 `sdd-version` の世代警告を warning にする

- **Decision**: `sdd-version` の major が現行プラグインより古い場合の重大度を warning とする。
- **Rationale**: major が古いことは「移行漏れの可能性」を示す advisory であり、トレーサビリティを破壊する構造的不備（error）ではない。
- **Rejected alternatives**: error として報告する — 構造的不備と同列に扱うことになり、重大度の意味が失われるため却下。
