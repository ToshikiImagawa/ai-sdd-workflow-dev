---
id: "adr-workflow-foundation-front-matter-recommend"
title: "front matter 推奨 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-workflow-foundation-front-matter-recommend"]
tags: ["front-matter", "metadata", "skill", "scan"]
category: "workflow-foundation"
---

# front matter 推奨 決定ログ

## 2026-07-24 skill として実装しモデルを haiku にする

- **Decision**: front matter 推奨機能を skill として実装し、`model: haiku` を指定する。
- **Rationale**: A-001（Skills-First）に従い skill として実装する。推論主体の軽量タスクであるため haiku で十分である。
- **Rejected alternatives**: legacy command として実装する — Skills-First の原則に反するため却下。

## 2026-07-24 走査をスクリプトに一括委譲する

- **Decision**: 対象文書の走査を Claude の逐次 Read ではなくスクリプトの一括走査で行う。
- **Rationale**: A-002 に従い決定的処理を委譲することで、ツール呼び出しとトークンを削減できる（NFR-002）。
- **Rejected alternatives**: Claude が逐次 Read する — ツール呼び出しとトークンを浪費するため却下。

## 2026-07-24 走査ロジックを共有モジュールに集約する

- **Decision**: front matter 検出・種別判定のロジックを本スキル固有実装にせず、`fm_parser` / `naming` / `doc_walker` の共有モジュールを利用する。
- **Rationale**: 他スキル・フックと同じロジックを共有することで、検出・種別判定の重複を排除できる。
- **Rejected alternatives**: スキル内に固有実装を持つ — 同じロジックが複数箇所に重複し更新漏れを招くため却下。

## 2026-07-24 既定を推奨のみとし適用は --apply の明示 opt-in にする

- **Decision**: 既定動作は推奨の提示のみとし、実際の付与は `--apply` の明示指定 + AskUserQuestion による確認を必須とする。
- **Rationale**: ファイル変更は破壊的操作であるため、安全側を既定とする必要がある。
- **Rejected alternatives**: 常に適用する — 確認なしにファイルを書き換えることになるため却下。

## 2026-07-24 front matter の検証は担当せず推奨・適用に限定する

- **Decision**: 本スキルは front matter の付与支援に限定し、検証は行わない。
- **Rationale**: 検証は quality-guardrails の front-matter-reviewer が担当する責務であり、分離することで重複を避けられる。
- **Rejected alternatives**: 本スキルで検証も実施する — 専用エージェントと責務が重複するため却下。

## 2026-09-02 後付け適用時は `sdd-version` フィールド自体を付与しない

- **Decision**: 既存文書への front matter 後付け適用時に、`sdd-version` フィールドを付与しない（フィールド自体を除外する）。
- **Rationale**: 現行バージョンを設定すると「現行世代で生成された」という偽の信号になり、front-matter-reviewer・doc-consistency-checker の世代判別・移行漏れ検知を汚染する。`"unknown"` のような不明値は semver 形式検証に例外を作ってしまう。フィールドを付与しない選択は既存の「不在 = 導入前」という規約と整合し、実装も最小になる。
- **Rejected alternatives**: 現行バージョンを設定する — 偽の世代信号となり移行漏れ検知を汚染するため却下。`"unknown"` 等の不明値を設定する — semver 形式検証に例外を作るため却下。
