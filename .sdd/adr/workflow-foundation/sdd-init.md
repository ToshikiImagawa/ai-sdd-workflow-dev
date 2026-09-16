---
id: "adr-workflow-foundation-sdd-init"
title: "プロジェクト初期化 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-workflow-foundation-sdd-init"]
tags: ["initialization", "template", "claude-md", "skill"]
category: "workflow-foundation"
---

# プロジェクト初期化 決定ログ

## 2026-07-24 skill として実装しモデルを haiku にする

- **Decision**: プロジェクト初期化を skill として実装し、`model: haiku` を指定する。
- **Rationale**: A-001（Skills-First）に従い skill として実装する。統括役であり軽量な haiku で足りる。
- **Rejected alternatives**: legacy command として実装する — Skills-First の原則に反するため却下。

## 2026-07-24 初期化を 2 フェーズスクリプト実行にする

- **Decision**: 初期化処理を Claude の逐次ツール実行ではなく、2 フェーズのスクリプト実行に分離する。
- **Rationale**: A-002 に従い決定的操作をスクリプトへ委譲することで、ツール呼び出しを 60〜70% 削減できる（NFR-002）。
- **Rejected alternatives**: Claude が逐次ツールを実行する — ツール呼び出しとトークンを浪費するため却下。

## 2026-07-24 CLAUDE.md を最小化し詳細を rules へ分離する

- **Decision**: CLAUDE.md に書く内容を最小限のセクションに留め、詳細ガイドは path-scoped rule ファイルへ分離する。
- **Rationale**: 常時ロードされるコンテキストを軽く保つ必要がある。詳細は `.sdd/**` 作業時のみロードされる path-scoped rule に置ける。
- **Rejected alternatives**: 詳細ガイドも CLAUDE.md に含める — 常時ロードのコンテキストが肥大化するため却下。

## 2026-07-24 詳細ルールを単一英語ファイルにする

- **Decision**: 詳細ルールファイルを en / ja の二本立てにせず、単一の英語ファイルとする。
- **Rationale**: rules は AI エージェント向けのガイドであり人間向けドキュメントではない。単一ファイルにすることで path-scoped rule を 1 本に保てる。
- **Rejected alternatives**: en / ja の二本立てにする — path-scoped rule が分岐し、AI 向けガイドとして不要な二重管理になるため却下。

## 2026-07-24 CONSTITUTION.md の生成を constitution init に委ねる

- **Decision**: CONSTITUTION.md の生成は sdd-init では行わず `constitution init` に委ね、sdd-init はテンプレート配置に限定する。
- **Rationale**: 原則はプロジェクト文脈に応じたカスタマイズが必要であり、テンプレート配置とは責務が異なる。
- **Rejected alternatives**: sdd-init が CONSTITUTION.md を生成する — 責務が混ざるため却下。

## 2026-07-24 詳細ルールの配置を session-start に担わせる

- **Decision**: 詳細ルールファイルの配置・更新を sdd-init ではなく session-start フックが担い、sdd-init は CLAUDE.md の最小セクションのみを扱う。
- **Rationale**: プラグインのバージョンに追随した更新はセッション開始ごとに必要であり、session-config の責務に属する。
- **Rejected alternatives**: sdd-init が配置する — 初期化を再実行しない限りバージョン追随更新が行われないため却下。
