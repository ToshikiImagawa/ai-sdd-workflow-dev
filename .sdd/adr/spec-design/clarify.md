---
id: "adr-spec-design-clarify"
title: "仕様明確化 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-08"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-spec-design-clarify"]
tags: ["clarification", "ambiguity-analysis", "clarity-score"]
category: "spec-design"
---

# 仕様明確化 決定ログ

## 2026-07-08 分析を clarification-assistant エージェントへ委譲する

- **Decision**: 曖昧点の分析をスキル単体で行わず、clarification-assistant エージェントに委譲する。
- **Rationale**: 分析をコンテキスト独立なエージェントへ委譲することで、メインのコンテキストを節約できる。
- **Rejected alternatives**: スキル単体で分析まで行う — メインコンテキストを分析の中間出力で消費するため却下。

## 2026-07-08 分析エージェントのツール権限を読み取り系に限定する

- **Decision**: clarification-assistant のツールを Read / Glob / Grep / AskUserQuestion に限定し、Task を与えない。
- **Rationale**: Task による再帰探索はコンテキスト爆発のリスクがあり、決定的な分析には不要である。
- **Rejected alternatives**: Task を含めて再帰探索を可能にする — コンテキスト爆発のリスクに見合う利点がないため却下。

## 2026-07-08 エージェントは提案のみ、編集はスキルが適用する

- **Decision**: エージェントは修正提案を返すのみとし、Edit / Write の適用はスキル側が行う。
- **Rationale**: 読み取り専用エージェントと編集権限を分離することで、意図しない書き込みを防げる（A-002）。
- **Rejected alternatives**: エージェントが直接ドキュメントを編集する — 意図しない書き込みを構造的に防げないため却下。

## 2026-07-08 implementation-ready の閾値を明確度 80% に固定する

- **Decision**: 明確度スコア 80% を implementation-ready の閾値とし、未満の場合は追加の明確化を推奨する。
- **Rationale**: 親 PRD の NFR_001 と B-001（Vibe Coding 防止）に基づき、基準未満での実装着手を防ぐ必要がある。
- **Rejected alternatives**: 閾値を可変にする — 基準が状況依存になり Vibe Coding 防止のゲートとして機能しないため却下。

## 2026-07-08 1 回に提示する質問を最大 5 問に制限する

- **Decision**: 1 回の提示で行う明確化質問を最大 5 問に制限する。
- **Rationale**: ユーザーの回答負担を抑え、高影響度の質問に集中させるため（NFR-003）。
- **Rejected alternatives**: 質問数を無制限にする — 回答負担が増え、重要な質問が埋もれるため却下。

## 2026-07-08 探索スコープを SDD_ROOT 配下に限定する

- **Decision**: ドキュメント探索の範囲を `SDD_ROOT`（既定 `.sdd/`）配下に限定する。
- **Rationale**: 対象外ファイルの走査によるノイズとコンテキストの浪費を防ぐため。
- **Rejected alternatives**: プロジェクト全体を探索する — ノイズとコンテキスト浪費が大きいため却下。

## 2026-09-02 設計ドラフトの参照パスをチケット単位の固定パスにする

- **Decision**: 参照する技術設計ドラフトを `task/{ticket-number}/design-draft.md` の固定パスとし、`ticket-number` 指定時のみ読み込む任意入力とする。
- **Rationale**: generate-spec の出力先と一致させる必要がある。また設計ドラフトは一時文書であるため、存在を前提とする必須入力にはできない。
- **Rejected alternatives**: 機能単位の `specification/*_design.md` を参照する — v5 では技術設計が永続文書ではなくチケット単位の一時ドラフトになったため却下。
