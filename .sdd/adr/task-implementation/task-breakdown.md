---
id: "adr-task-implementation-task-breakdown"
title: "タスク分解 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-task-implementation-task-breakdown"]
tags: ["task-breakdown", "tasks"]
category: "task-implementation"
---

# タスク分解 決定ログ

## 2026-07-24 スキル単体で実装しエージェントを分離しない

- **Decision**: タスク分解をスキル単体で実装する。
- **Rationale**: 設計ドラフトの分析と分解は単一スキルで完結するため。
- **Rejected alternatives**: スキル + エージェント構成にする — 分離の必要がないため却下。

## 2026-07-24 ツール権限から Bash を外す

- **Decision**: `allowed-tools` を `Read, Glob, Grep, AskUserQuestion, Edit(.sdd/**)` とし Bash を含めない。
- **Rationale**: 分解処理は決定的コマンドの実行を要さず、生成は Edit で行える。
- **Rejected alternatives**: Bash を含める — 不要な権限を事前承認することになるため却下。

## 2026-07-24 設計ドラフト欠如時の挙動をモードで分岐する

- **Decision**: 設計ドラフトが存在しない場合、`--ci` ではエラー終了し、対話モードでは generate-spec の実行を促す。
- **Rationale**: CI では確定的に失敗させる必要があり、対話では次アクションを案内する方が有用である（FR-002）。
- **Rejected alternatives**: 常にエラーにする — 対話モードで次アクションを案内できないため却下。

## 2026-07-24 依存関係を Mermaid 図で表現する

- **Decision**: タスク間の依存関係をテキストだけでなく Mermaid の依存関係図で表現する。
- **Rationale**: 依存を可視化して実装順序の錯綜を防ぐため。
- **Rejected alternatives**: テキストのみで表現する — 依存の把握が難しく実装順序を誤るため却下。

## 2026-07-24 Serena MCP を任意連携にする

- **Decision**: Serena MCP を必須とせず任意連携とし、未設定でも動作させる。
- **Rationale**: 精度向上は歓迎するが、外部 MCP への依存を必須にはしない。
- **Rejected alternatives**: Serena を必須にする — 非導入環境で動作しなくなるため却下。

## 2026-07-24 カバレッジ検証を PRD / spec 存在時のみ行う

- **Decision**: FR / NFR / API のカバレッジ検証を、PRD または spec が存在する場合のみ実施する。
- **Rationale**: 上流要求がある場合にのみカバレッジを担保できる（FR-005）。
- **Rejected alternatives**: 常時検証する — 上流要求が無い場合に検証基準が存在しないため却下。

## 2026-09-02 設計ドラフトの参照パスをチケット単位の固定パスにする

- **Decision**: 参照する設計ドラフトを `task/{ticket}/design-draft.md` のチケット単位固定パスとする。
- **Rationale**: generate-spec の出力先と一致させる必要がある。設計ドラフトはチケット単位の一時文書であり、抽象仕様書のフラット / 階層構造とは独立している。
- **Rejected alternatives**: 機能単位の `specification/*_design.md` を参照する — v5 の出力先と食い違うため却下。

## 2026-09-02 `ticket-number` を必須引数にする

- **Decision**: `ticket-number` を任意ではなく必須の引数とする。
- **Rationale**: 設計ドラフトの位置と tasks.md の保存先が共にチケット番号で決まるため、省略できない。
- **Rejected alternatives**: 任意引数にする — 入力・出力の位置が決まらないため却下。
