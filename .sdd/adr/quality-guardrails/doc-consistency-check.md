---
id: "adr-quality-guardrails-doc-consistency-check"
title: "ドキュメント間整合性チェック 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-07"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-quality-guardrails-doc-consistency-check"]
tags: ["consistency-check", "quality-gate"]
category: "quality-guardrails"
---

# ドキュメント間整合性チェック 決定ログ

## 2026-07-07 整合性チェックを Markdown プロンプトスキルとして実装する

- **Decision**: ドキュメント間整合性チェックを、決定的なフックスクリプトではなく Markdown プロンプトスキルとして実装する。
- **Rationale**: 意味的な読解・比較・分類は決定的スクリプトでは表現できず、Claude の判断が必要である（A-001 Skills-First）。
- **Rejected alternatives**: hook スクリプトで実装する — 意味的な比較を決定的処理で表現できないため却下。agent として実装する — 自動起動されるチェックの形態としてスキルが適するため採用しなかった。

## 2026-07-07 自動実行のみとし user-invocable: false にする

- **Decision**: 本スキルを `user-invocable: false` とし、自動実行のみで起動させる。手動チェックは `/check-spec` に分離する。
- **Rationale**: 親 PRD の FR_001 が「トリガー方式: 自動、ユーザー呼び出し不可」を要求している。
- **Rejected alternatives**: `user-invocable: true` にする — PRD の定義に反し、`/check-spec` と役割が重複するため却下。

## 2026-07-07 ツール権限を読み取り専用にする

- **Decision**: 本スキルのツール権限を Read / Glob / Grep の読み取り専用に限定する。
- **Rationale**: 検出専任であり自動修正しないという責務を構造的に保証できる。DC_001（ブロッキング最小化）とも整合する。
- **Rejected alternatives**: 読み書き可にする — 検出専任の責務を構造的に保証できないため却下。

## 2026-07-07 front matter 検証を front-matter-reviewer へ委譲する

- **Decision**: front matter の検証は本スキルでは行わず、front-matter-reviewer に委譲する。
- **Rationale**: 責務分離（A-002）に従い、本スキルは本文の内容整合性に専念して重複検証を避ける。
- **Rejected alternatives**: 本スキルで front matter も検証する — 専用エージェントと検証が重複するため却下。

## 2026-07-07 不整合検出時の優先方針を上流優先とする

- **Decision**: 不整合を検出した際の正の判断を上流優先（PRD > spec > design）とする。
- **Rationale**: 実装が正で spec が古い場合もあるため、一律に spec を正とはできない。
- **Rejected alternatives**: 一律 spec を正とする — 実装が正で spec が古いケースを誤判定するため却下。

## 2026-07-07 共通参照資料を shared/references/ に一元化し symlink で参照する

- **Decision**: 依存関係・パス解決手順などの共通参照資料を `shared/references/` に置き、スキルからは symlink で参照する。
- **Rationale**: これらの参照資料は複数スキルで共通であり、一元化しないと重複と更新漏れが生じる。
- **Rejected alternatives**: スキルごとに複製する — 重複と更新漏れを招くため却下。

## 2026-09-02 design ↔ 実装チェックを impl-spec-check に一本化する

- **Decision**: design ↔ 実装の整合チェックを本スキルのスコープから除外し、`impl-spec-check`（`/check-spec`）に一本化する。
- **Rationale**: 親 PRD が design ↔ 実装チェックを明示的に `impl-spec-check` の責務と定義しており、旧 FR-004 はこれと矛盾していた。同じ検出を advisory hook（本スキル）と明示実行（`/check-spec`）の二経路で行う多重防御は責務分離（A-002）に反するため、確実な明示実行の側に一本化する。
- **Rejected alternatives**: 本スキルでも design ↔ 実装を検出する — PRD の責務定義に反し、多重防御が責務分離を崩すため却下。

## 2026-09-02 世代列挙（FR-007）の入力を documentation-index の index に依存させる

- **Decision**: `sdd-version` の世代列挙を独自の全文書走査では行わず `documentation-index` の index を利用し、`SDD_INDEX=off` の場合はこのチェックをスキップする。
- **Rationale**: 独自走査は本スキルが避けてきた「決定的な全文書走査コスト」を再導入し、A-002（機械的処理はスクリプト・インデックス側に委譲）に反する。index 依存にすることで軽量な advisory チェックという性質を保てる。トレードオフとして index 無効時は世代列挙のみ機能しないが、他のチェック項目には影響しない。
- **Rejected alternatives**: 独自に Glob / Grep で全文書の front matter を走査する — 全文書走査コストを再導入し責務分離に反するため却下。
