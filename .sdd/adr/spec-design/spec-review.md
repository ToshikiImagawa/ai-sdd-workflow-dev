---
id: "adr-spec-design-spec-review"
title: "仕様・設計レビュー 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-08"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-spec-design-spec-review"]
tags: ["spec-review", "agent", "constitution", "traceability"]
category: "spec-design"
---

# 仕様・設計レビュー 決定ログ

## 2026-07-08 レビューをスキルではなくサブエージェントとして実装する

- **Decision**: 仕様・設計レビューを skill ではなく agent（サブエージェント）として実装する。
- **Rationale**: レビューは対話補助を伴う文書横断分析であり、宣言的なサブエージェントの形態が適する。
- **Rejected alternatives**: skill として実装する — 文書横断分析を独立コンテキストで行えないため却下。

## 2026-07-08 レビューエージェントのモデルを Sonnet にする

- **Decision**: spec-reviewer のモデルを Sonnet とする。
- **Rationale**: 原則解釈と複数文書のトレーサビリティ判定という多段階分析に必要な推論能力を確保する必要がある。
- **Rejected alternatives**: Haiku — 多段階の原則解釈に推論能力が足りないため却下。Opus — 本用途に対して過剰なコストとなるため却下。

## 2026-07-08 サブエージェント内で Task を使わず自己完結させる

- **Decision**: レビューエージェントは Task による再帰探索を行わず、自己完結して分析する。
- **Rationale**: 文書レベルのトレーサビリティ検証で Task 再帰探索を行うとコンテキストが急増するため。
- **Rejected alternatives**: Task で再帰探索する — コンテキストが急増し、得られる精度に見合わないため却下。

## 2026-07-08 front matter 検証を front-matter-reviewer へ委譲する

- **Decision**: front matter の形式・依存方向・id 一意性の検証は本エージェントでは行わず、front-matter-reviewer に委譲する。
- **Rationale**: front matter 検証は独立した責務であり、専用エージェントに委譲することで実装の重複を避けられる。
- **Rejected alternatives**: 本機能内で front matter も検証する — 専用エージェントと検証ロジックが重複するため却下。

## 2026-07-08 修正提案を意図変更を伴わない範囲に限定する

- **Decision**: 自動の修正提案は意図変更を伴わない範囲に限定し、アーキテクチャ再設計・技術選定変更・ビジネスロジック変更は手動修正またはユーザー確認を推奨する。
- **Rationale**: 意図に踏み込む変更を AI が提案として確定させると、人間の判断を経ずに仕様の意味が変わり得る（B-001 Vibe Coding 防止）。
- **Rejected alternatives**: 全指摘に対して修正提案を出す — 意図変更が人間の判断を経ずに入り込むため却下。

## 2026-07-08 出力エンコーディングを UTF-8 に維持する

- **Decision**: レビュー出力を ASCII エスケープせず UTF-8 で出力する。
- **Rationale**: 日本語レビュー出力の文字化けを防止する必要がある（T-003）。
- **Rejected alternatives**: ASCII エスケープして出力する — 日本語出力が可読でなくなるため却下。
