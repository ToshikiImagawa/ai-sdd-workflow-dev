---
id: "adr-quality-guardrails-vibe-detection"
title: "Vibe Coding 兆候検知 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-07"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-quality-guardrails-vibe-detection"]
tags: ["vibe-coding-prevention", "hooks", "ambiguity-detection"]
category: "quality-guardrails"
---

# Vibe Coding 兆候検知 決定ログ

## 2026-07-07 機械的検知をフックに、判断をスキルに分離する

- **Decision**: 曖昧表現の機械的検知を Python フックで行い、内容の判断はスキル側に分離する。
- **Rationale**: 決定的な検知を LLM に委ねるとトークンの浪費と応答遅延を招く（A-002）。
- **Rejected alternatives**: 検知と判断の両方をスキル（LLM）で行う — 決定的処理にトークンと遅延のコストを払うことになるため却下。

## 2026-07-07 非ブロッキングの additionalContext で注入する

- **Decision**: 検知結果を `deny` ではなく `additionalContext` による非ブロッキング注入で伝える。
- **Rationale**: プロンプトの拒否は開発フローを阻害し、B-001（Vibe Coding 防止）の趣旨である「明確化の促進」を超えた介入になる（DC_001）。
- **Rejected alternatives**: `deny` でプロンプトをブロックする — 開発フローを阻害し、原則の趣旨を超えるため却下。

## 2026-07-07 日英のパターンを同一集合に内包する

- **Decision**: 入力言語を判定して切り替えるのではなく、日英の曖昧表現パターンを同一のパターン集合に内包する。
- **Rationale**: 言語判定のコストを排して 500ms の応答要件を満たすため。取りこぼしよりも誤検知を許容する設計方針を取る。
- **Rejected alternatives**: 入力言語を判定して辞書を切り替える — 判定コストで応答要件を満たせなくなるため却下。

## 2026-07-07 一致なしの場合は無出力とする

- **Decision**: 曖昧表現に一致しない場合は return して何も出力しない。
- **Rationale**: ノイズを避け、明確な指示による開発フローには一切介入しないため（FR-005）。
- **Rejected alternatives**: 常に何らかの出力を行う — 明確な指示に対してもノイズを出すため却下。

## 2026-07-07 フック出力を ensure_ascii=False にする

- **Decision**: フックの JSON 出力を `ensure_ascii=False`（UTF-8）で行う。
- **Rationale**: 日本語の一致文字列を `additionalContext` に文字化けなく含める必要がある（T-003）。
- **Rejected alternatives**: `ensure_ascii=True` — 日本語がエスケープされ可読性を失うため却下。
