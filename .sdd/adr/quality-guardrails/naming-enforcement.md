---
id: "adr-quality-guardrails-naming-enforcement"
title: "ファイル命名規則の強制 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-08"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-quality-guardrails-naming-enforcement"]
tags: ["hooks", "naming-convention", "quality-gate"]
category: "quality-guardrails"
---

# ファイル命名規則の強制 決定ログ

## 2026-07-08 命名検証をフック（Python）に実装する

- **Decision**: 命名規則の検証を LLM スキルではなく Python のフックスクリプトに実装する。
- **Rationale**: 決定的なサフィックス照合を LLM に委ねるとトークンの浪費と応答遅延を招く（A-002）。
- **Rejected alternatives**: スキル（LLM）で検証する — 決定的処理にトークンと遅延のコストを払うことになるため却下。

## 2026-07-08 命名規則違反のみ deny でブロックする

- **Decision**: 命名規則違反を検出した場合は `deny` で書き込みをブロックする。
- **Rationale**: 命名規則違反はワークフロー整合性を破壊するため確実なブロックが必要である。DC_001（ブロッキングの最小化）の下で、これが唯一の例外領域である。
- **Rejected alternatives**: 非ブロッキング警告に留める — 違反ファイルが生成されワークフロー整合性が壊れるため却下。

## 2026-07-08 検証を書き込み前（PreToolUse）に行う

- **Decision**: 命名検証を PreToolUse フックで書き込み前に行う。
- **Rationale**: 違反ファイルの生成そのものを防ぐ必要がある。書き込み後の検証では違反ファイルが一度生成されてしまう。
- **Rejected alternatives**: 書き込み後に検証する — 違反ファイルが一度生成されてしまうため却下。

## 2026-07-08 検証対象を `.md` のみに限定する

- **Decision**: 命名検証の対象拡張子を `.md` のみとする。
- **Rationale**: `.sdd/` のドキュメントは Markdown であり、図表・補助ファイル等の非 `.md` は命名規則の対象外である。
- **Rejected alternatives**: 全ファイルを対象にする — 命名規則の対象外ファイルまでブロックすることになるため却下。

## 2026-07-08 ディレクトリ名を `.sdd-config.json` から解決する

- **Decision**: 検証に用いるディレクトリ名をハードコードせず `.sdd-config.json` から解決し、設定が無い場合は既定値を用いる。
- **Rationale**: プロジェクト固有のディレクトリ名に追従する必要がある。既定値を持つことで設定なしのゼロ設定動作も維持できる。
- **Rejected alternatives**: ディレクトリ名をハードコードする — プロジェクト固有の構成に追従できないため却下。

## 2026-07-08 管理対象外パスは無出力で許可する

- **Decision**: `.sdd/` 外や `task/` 配下など管理対象外のパスへの書き込みには一切出力せず許可する。
- **Rationale**: 無関係な書き込みに介入しないことで開発フローへのノイズを避ける（FR-005）。
- **Rejected alternatives**: 対象外でも何らかの出力を行う — 無関係な編集にノイズを出すため却下。

## 2026-09-02 無視パターンの照合を fnmatch（glob）で行う

- **Decision**: 無視パターンの照合方式を `fnmatch`（glob）とする。
- **Rationale**: 既存実装（`find-implementation-files.py`）と同じ照合方式を採用することで、実装と設定記述の一貫性を保てる（FR-006）。正規表現よりエスケープが不要で書きやすい。
- **Rejected alternatives**: 正規表現で照合する — エスケープが必要で設定記述が煩雑になり、既存実装と方式が揃わないため却下。単純な前方一致 — 表現力が不足するため却下。
