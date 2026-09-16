---
id: "adr-task-implementation-checklist-generation"
title: "チェックリスト生成 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-task-implementation-checklist-generation"]
tags: ["checklist", "quality"]
category: "task-implementation"
---

# チェックリスト生成 決定ログ

## 2026-07-24 スキル単体で実装しエージェントを分離しない

- **Decision**: チェックリスト生成をスキル単体で実装し、分析専用エージェントを分離しない。
- **Rationale**: 観点抽出・分類は単一スキルで完結するため、エージェントを分ける必要がない。
- **Rejected alternatives**: スキル + 分析エージェント構成にする — 分離の必要がなく構成が複雑になるだけのため却下。

## 2026-07-24 ツール権限から Bash を外し書き込みを `.sdd/` に限定する

- **Decision**: `allowed-tools` を `Read, Glob, Grep, Edit(.sdd/**)` とし、Bash を含めない。
- **Rationale**: チェックリスト生成は決定的コマンドの実行を要さない。生成は Edit で行い、事前承認は `.sdd/` 配下に限定する。
- **Rejected alternatives**: Bash を含める — 不要な権限を事前承認することになるため却下。

## 2026-07-24 チェックリスト ID をカテゴリ + 連番にする

- **Decision**: チェックリスト項目の ID を `CHK-{category}{nn}` 形式とする。
- **Rationale**: カテゴリをプレフィックスに含めることで、更新時の ID 安定性と分類の可読性を両立できる（NFR-001）。
- **Rejected alternatives**: 通し連番のみにする — 項目の追加・削除で ID が動き、分類も読み取れないため却下。

## 2026-07-24 チェックリストの保存先を task ディレクトリ配下に固定する

- **Decision**: チェックリストの保存先を `${SDD_TASK_PATH}/{ticket}/checklist.md` に固定する。
- **Rationale**: run-checklist の入力位置と一致させることでワークフロー連携が成立する（親 PRD IR_001）。
- **Rejected alternatives**: 任意パスに保存する — run-checklist との連携が成立しないため却下。

## 2026-09-02 抽出元は `*_spec.md` のみを必須とする

- **Decision**: 観点の抽出元として `*_spec.md` を必須とし、PRD・設計ドラフト・tasks は任意入力とする。設計ドラフト不在時は仕様書のみで続行する。
- **Rationale**: 仕様は検証観点の中核であり永続文書である。一方、設計ドラフトは実装完了後に削除される一時文書であるため必須にできない。
- **Rejected alternatives**: 全文書を必須にする — 一時文書である設計ドラフトの不在で生成が止まるため却下。

## 2026-09-02 設計ドラフトの参照パスをチケット単位の固定パスにする

- **Decision**: 参照する設計ドラフトを `task/{ticket}/design-draft.md` のチケット単位固定パスとする。
- **Rationale**: generate-spec / task-breakdown / implement と同一のパスを参照することで、順方向フローで参照先が食い違わない。
- **Rejected alternatives**: 機能単位の `specification/*_design.md` を参照する — v5 の出力先と食い違うため却下。
