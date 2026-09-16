---
id: "adr-workflow-foundation-constitution-management"
title: "プロジェクト原則管理 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-workflow-foundation-constitution-management"]
tags: ["constitution", "governance", "skill", "principles"]
category: "workflow-foundation"
---

# プロジェクト原則管理 決定ログ

## 2026-07-24 原則管理を legacy command ではなく skill として実装する

- **Decision**: 原則管理機能を legacy command ではなく `skills/` 配下の skill として実装する。
- **Rationale**: A-001（Skills-First）に従い、新規機能は skill として実装する方針である。
- **Rejected alternatives**: legacy command として実装する — Skills-First の原則に反するため却下。

## 2026-07-24 validate の走査をスクリプトに一括委譲する

- **Decision**: 原則参照の走査を Claude の Glob / Grep による逐次走査ではなく、スクリプトによる一括走査で行う。
- **Rationale**: A-002 に従い決定的処理をスクリプトへ委譲することで、Claude のツール呼び出しとトークンを削減できる（NFR-001）。
- **Rejected alternatives**: Claude が Glob / Grep で逐次走査する — ツール呼び出しとトークンを浪費するため却下。

## 2026-07-24 走査スクリプトを Python 標準ライブラリで実装する

- **Decision**: 走査スクリプトを Bash + find/grep ではなく Python 標準ライブラリで実装する。
- **Rationale**: OS 固有 CLI に依存しないことで、対応 OS 間の挙動を等価にできる（NFR-002。cross-platform-portability と整合）。
- **Rejected alternatives**: Bash + find/grep — OS 固有 CLI の挙動差で移植性を損なうため却下。

## 2026-07-24 init は既存ファイルが存在する場合スキップする

- **Decision**: `constitution init` は CONSTITUTION.md が既に存在する場合、上書きせずスキップする。
- **Rationale**: 既存の原則を尊重し、利用者のカスタマイズを破壊しないため（FR-007）。
- **Rejected alternatives**: 上書きする — 利用者のカスタマイズを破壊するため却下。

## 2026-07-24 CONSTITUTION.md の生成を constitution init が担う

- **Decision**: CONSTITUTION.md の生成は sdd-init ではなく `constitution init` が担い、sdd-init はテンプレート配置のみに限定する。
- **Rationale**: 原則はプロジェクト文脈に応じたカスタマイズが必要であり、テンプレート配置と原則生成は責務が異なる。
- **Rejected alternatives**: sdd-init が CONSTITUTION.md を生成する — 責務が混ざり、文脈に応じたカスタマイズの導線が失われるため却下。
