---
id: "adr-quality-guardrails-stale-doc-detection"
title: "ドキュメント更新漏れ検知 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-08"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-quality-guardrails-stale-doc-detection"]
tags: ["hooks", "consistency-check", "quality-gate"]
category: "quality-guardrails"
---

# ドキュメント更新漏れ検知 決定ログ

## 2026-07-08 パス判定をフック（Python）に実装する

- **Decision**: 更新漏れ検知のパス判定を LLM スキルではなく Python のフックに実装する。
- **Rationale**: 決定的なパス判定を LLM に委ねるとトークンの浪費と応答遅延を招く（A-002）。
- **Rejected alternatives**: スキル（LLM）で判定する — 決定的処理にトークンと遅延のコストを払うことになるため却下。

## 2026-07-08 非ブロッキングの additionalContext で促す

- **Decision**: 更新漏れの検知結果を `deny` ではなく `additionalContext` による非ブロッキング注入で伝える。
- **Rationale**: 編集後の更新漏れは警告に留め、修正判断は開発者と AI に委ねるべきである（DC_001）。
- **Rejected alternatives**: `deny` でブロックする — 編集後の警告事項で開発フローを止めることになるため却下。

## 2026-07-08 フックは促しのみを行い整合性は検証しない

- **Decision**: フックは対応ドキュメントの更新を促すのみとし、実際の整合性検証は検証スキルへ誘導する。
- **Rationale**: 整合性検証は子 PRD のスコープ外であり、doc-consistency-checker 等が担う責務である。
- **Rejected alternatives**: フックで整合性を検証する — 責務がスコープ外であり、決定的フックで意味的検証を行うことになるため却下。

## 2026-07-08 ソース → 設計書の対応を basename の walk 探索で解決する

- **Decision**: ソースファイルから対応ドキュメントを探す方式を、パスマッピング表ではなく basename による `os.walk` 探索とする。
- **Rationale**: 階層構造・フラット構造の双方で対応ドキュメントを発見でき、設定が不要になる。
- **Rejected alternatives**: パスマッピング表を持つ — プロジェクトごとの設定が必要になり、階層・フラット両構造への追従も手作業になるため却下。

## 2026-07-08 該当なしの場合は無出力とする

- **Decision**: 対応ドキュメントが見つからない場合は return して何も出力しない。
- **Rationale**: 無関係な編集にノイズを出さず開発フローに介入しないため（FR-005）。
- **Rejected alternatives**: 常に何らかの出力を行う — 無関係な編集にノイズを出すため却下。

## 2026-07-08 フック出力を ensure_ascii=False にする

- **Decision**: フックの JSON 出力を `ensure_ascii=False`（UTF-8）で行う。
- **Rationale**: パスに含まれる日本語を `additionalContext` に文字化けなく含める必要がある（T-003）。
- **Rejected alternatives**: `ensure_ascii=True` — 日本語パスがエスケープされ可読性を失うため却下。
