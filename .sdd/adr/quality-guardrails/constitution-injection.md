---
id: "adr-quality-guardrails-constitution-injection"
title: "CONSTITUTION 原則の自動注入 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-08"
updated: "2026-07-08"
sdd-version: "5.0.0"
depends-on: ["spec-quality-guardrails-constitution-injection"]
tags: ["hooks", "constitution", "context-injection"]
category: "quality-guardrails"
---

# CONSTITUTION 原則の自動注入 決定ログ

## 2026-07-08 原則の注入を編集前（PreToolUse）に行う

- **Decision**: CONSTITUTION 原則の注入を PreToolUse フックで、編集の前に行う。
- **Rationale**: 原則は実装着手時点で参照させる必要があり、編集後の注入では手戻りになる。
- **Rejected alternatives**: 編集後（PostToolUse）に注入する — 原則違反の指摘が手戻りになるため却下。

## 2026-07-08 注入を非ブロッキングの additionalContext で行う

- **Decision**: 原則注入は `additionalContext` による非ブロッキング注入とし、編集を `deny` でブロックしない。
- **Rationale**: 編集拒否は開発フローを阻害し、注入の目的（原則の提示）には不要である（DC_001 ブロッキングの最小化）。
- **Rejected alternatives**: `deny` で編集をブロックする — 開発フローを阻害し、目的に対して過剰なため却下。

## 2026-07-08 セッションマーカーで重複注入を抑止する

- **Decision**: `session_id` をキーとする一時ファイルのマーカーを用いて、セッション内の重複注入を抑止する。
- **Rationale**: 状態を持たない実装では全ソース編集で注入が走り、恒常的にコンテキストを消費する（DC_002）。
- **Rejected alternatives**: 状態を持たず毎回注入する — 恒常的にコンテキストを消費するため却下。

## 2026-07-08 注入量を 3,000 文字上限の切り詰めで制御する

- **Decision**: CONSTITUTION 本文の注入を 3,000 文字上限で切り詰め、末尾に全文参照への案内を添える。
- **Rationale**: 注入量の制御は必要だが、要約方式は LLM 呼び出しによるコストと遅延を招く。切り詰めは決定的で軽量である（DC_002）。
- **Rejected alternatives**: 全文を注入する — コンテキスト消費が大きいため却下。LLM で要約する — コストと遅延を招くため却下。

## 2026-07-08 注入対象を拡張子ホワイトリスト + `.sdd/` 除外に絞る

- **Decision**: 注入対象をソースコードの拡張子ホワイトリスト（`SOURCE_EXTENSIONS`）に限定し、`.sdd/` 配下を除外する。
- **Rationale**: ドキュメント編集時の原則注入は不要であり、コンテキストを浪費する（FR-005）。
- **Rejected alternatives**: 全ファイルを対象にする — ドキュメント編集でもコンテキストを浪費するため却下。

## 2026-07-08 注入の JSON 出力を ensure_ascii=False にする

- **Decision**: フックの JSON 出力を `ensure_ascii=False`（UTF-8）で行う。
- **Rationale**: 日本語を含む CONSTITUTION 本文を文字化けなく注入する必要がある（T-003）。
- **Rejected alternatives**: `ensure_ascii=True` — 日本語本文がエスケープされ可読性を失うため却下。
