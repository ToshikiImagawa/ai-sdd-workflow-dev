---
id: "adr-workflow-foundation-documentation-index"
title: "ドキュメントインデックス 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-14"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-workflow-foundation-documentation-index"]
tags: ["index", "hooks", "token-reduction", "session-config"]
category: "workflow-foundation"
---

# ドキュメントインデックス 決定ログ

## 2026-07-14 中間ストアを SQLite にする

- **Decision**: インデックスの中間ストアをプレーン JSON ではなく SQLite（スキーマ v1）とする。
- **Rationale**: 構造化データの集約・関係表現・部分更新に適しており、Python 標準ライブラリのみで動作する。
- **Rejected alternatives**: プレーン JSON — 部分更新と関係表現に適さないため却下。

## 2026-07-14 消費形式をテーブル形式 Markdown の派生物にする

- **Decision**: 消費側は SQLite を直接参照せず、テーブル形式の Markdown を派生生成して参照する。
- **Rationale**: 消費側（LLM）は Markdown を 1 回 Read するのが最も低コストである（NFR-001）。
- **Rejected alternatives**: SQLite を直接参照させる — LLM から参照するコストが高いため却下。

## 2026-07-14 キャッシュ無効化を SHA-256 コンテンツハッシュで判定する

- **Decision**: キャッシュの無効化判定を更新時刻ではなく SHA-256 のコンテンツハッシュで行う。
- **Rationale**: 内容の変化のみを検知でき再現性がある。時刻依存の誤検知を避けられる（FR-004）。
- **Rejected alternatives**: ファイル更新時刻で判定する — 内容が変わらない更新で誤検知するため却下。

## 2026-07-14 増分更新のガードを DB 存在チェックで行う

- **Decision**: 増分更新の実行可否を設定フラグ参照ではなく DB の存在チェックで判定し、DB が無ければ `update_one` の冒頭で return する。
- **Rationale**: 無効時は DB が存在しないため自動的に no-op となり、設定の二重管理を避けて off と自然に連動する（FR-005）。
- **Rejected alternatives**: 設定フラグを参照する — 設定の二重管理になるため却下。

## 2026-07-14 インデックスの既定を on にする

- **Decision**: インデックス機能の有効判定の既定値を on とし、無効化は `index: false` で明示させる。
- **Rationale**: トークン削減効果を標準で享受できるようにするため（session-config FR_001_04 / 子 PRD DC_001）。
- **Rejected alternatives**: 既定を off にする — トークン削減効果が標準で得られないため却下。

## 2026-07-14 派生生成の失敗時は警告して継続する

- **Decision**: インデックス派生生成の失敗時は例外を送出せず、try/except で警告を出して処理を継続する。
- **Rationale**: 派生生成の失敗がワークフローを止めないようにするため（FR-006 / 親 PRD DC_002）。
- **Rejected alternatives**: 例外を送出する — 補助機能の失敗でワークフローが止まるため却下。

## 2026-07-14 派生物の出力を UTF-8（ensure_ascii=False）にする

- **Decision**: 派生物の出力を `ensure_ascii=False`（UTF-8）で行う。
- **Rationale**: 日本語ドキュメントのタイトル・パスを派生物に文字化けなく含める必要がある（T-003）。
- **Rejected alternatives**: `ensure_ascii=True` — 日本語がエスケープされ可読性を失うため却下。

## 2026-09-02 `sdd_version` 列追加を SCHEMA_VERSION bump による全再構築で行う

- **Decision**: `sdd_version` 列の追加を `ALTER TABLE` ではなく `SCHEMA_VERSION` を `1` → `2` に bump して全再構築する方式で行う。
- **Rationale**: 既存の `init_schema` が version 不一致時に `DROP TABLE` → 再作成する既存パターンを踏襲でき、列追加のたびに個別マイグレーションを書く複雑さを避けられる（FR-007）。
- **Rejected alternatives**: `ALTER TABLE` で列追加する — 列追加ごとに個別マイグレーションが必要になり複雑さが増すため却下。
