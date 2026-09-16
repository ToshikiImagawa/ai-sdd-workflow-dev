---
id: "adr-task-implementation-run-checklist"
title: "チェックリスト自動検証 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-task-implementation-run-checklist"]
tags: ["checklist", "verification"]
category: "task-implementation"
---

# チェックリスト自動検証 決定ログ

## 2026-07-24 実行モデルを haiku にする

- **Decision**: run-checklist のモデルを `haiku` とする。
- **Rationale**: 検証はコマンド駆動で判断が比較的定型であり、軽量モデルでコスト効率を優先できる。
- **Rejected alternatives**: 既定モデルを使う — 定型的な検証に対して過剰なコストとなるため却下。

## 2026-07-24 検証コマンド定義を references に外出しする

- **Decision**: 検証コマンドのマッピングを SKILL.md 内に直書きせず `references/verification_commands.md` に外出しする。
- **Rationale**: マッピングの決定性・保守性を確保し、SKILL.md を簡潔に保つため（A-002）。
- **Rejected alternatives**: SKILL.md 内に直書きする — プロンプトが肥大化し保守性が落ちるため却下。

## 2026-07-24 項目の失敗時も中断せず継続する

- **Decision**: 検証項目が失敗しても即中断せず、失敗を記録して次の項目へ進む。
- **Rationale**: 1 項目の失敗で全体を止めず、全体の品質状況を把握できるようにするため（NFR-001）。
- **Rejected alternatives**: 即中断する — 全体の品質状況が把握できないため却下。

## 2026-07-24 未導入ツールを SKIPPED として扱う

- **Decision**: 検証に必要なツールが未導入の場合はエラーとせず SKIPPED とし、理由と導入提案を添える。
- **Rationale**: 環境依存を許容し、対象プロジェクトのツール構成に依存しない動作にするため（NFR-003）。
- **Rejected alternatives**: エラーとして扱う — ツール構成の違いだけで検証全体が失敗するため却下。

## 2026-07-24 進捗を TaskList でカテゴリ別に管理する

- **Decision**: 検証の進捗を TaskList でカテゴリ別に管理する。
- **Rationale**: 検証カテゴリごとの進捗を可視化するため。
- **Rejected alternatives**: 進捗管理を行わない — カテゴリごとの進捗が見えないため却下。
