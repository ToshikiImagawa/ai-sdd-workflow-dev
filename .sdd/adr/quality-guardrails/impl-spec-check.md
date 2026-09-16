---
id: "adr-quality-guardrails-impl-spec-check"
title: "実装と仕様の整合性チェック 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-07"
updated: "2026-09-10"
sdd-version: "5.0.0"
depends-on: ["spec-quality-guardrails-impl-spec-check"]
tags: ["consistency-check", "design-sync", "quality-gate"]
category: "quality-guardrails"
---

# 実装と仕様の整合性チェック 決定ログ

## 2026-07-07 トリガーを手動スキル呼び出し（`/check-spec`）にする

- **Decision**: 整合性チェックをフックの自動発火ではなく、手動スキル呼び出し（`/check-spec`）で起動する。
- **Rationale**: 整合性チェックは実行コストが高く、任意のタイミングで行うべきである。PRD FR_001 の手動トリガー方式に準拠する。
- **Rejected alternatives**: フックで自動発火する — 実行コストの高い処理が意図しないタイミングで走るため却下。

## 2026-07-07 ファイル走査をスクリプトに委譲する

- **Decision**: 対象ファイルの走査を Claude の Glob / Grep ではなく `find-spec-docs.py` に委譲する。
- **Rationale**: 決定的操作はスクリプトに委譲してトークンを節約する（A-002）。
- **Rejected alternatives**: Claude の Glob / Grep で走査する — 決定的操作にトークンを消費するため却下。

## 2026-07-07 検出・報告のみを行い自動修正しない

- **Decision**: 乖離の検出・報告のみを行い、自動修正は行わない（読み取り専用）。
- **Rationale**: 修正判断は開発者と AI の対話に委ねるべきであり、子 PRD のスコープ外でもある。読み取り専用とすることで安全性を担保できる。
- **Rejected alternatives**: 検出に加えて自動修正する — 修正判断を人間の対話から切り離すことになるため却下。

## 2026-07-07 ドキュメント間整合性を `--full` 時に spec-reviewer へ委譲する

- **Decision**: ドキュメント間整合性の検証は本スキルでは行わず、`--full` 指定時に `spec-reviewer` へ委譲する。
- **Rationale**: 本スキルは spec ↔ 実装に責務を特化させ、品質レビューは既存エージェントを再利用する（責務の分離）。
- **Rejected alternatives**: 本スキルでドキュメント間整合性も実施する — 既存エージェントと責務が重複するため却下。

## 2026-07-07 シンボル解析の Serena 連携を任意にする

- **Decision**: Serena MCP によるシンボル解析を任意連携とし、未設定時は Grep / Glob にフォールバックする。
- **Rationale**: Serena 非導入環境でも言語非依存で動作させる必要がある。
- **Rejected alternatives**: Serena を常時必須にする — 非導入環境で機能しなくなるため却下。

## 2026-07-07 本機能は実装からの逆算記述とし、以降は spec を真実の源とする

- **Decision**: 本機能の spec / design を既存実装からの逆算記述として作成し、以降は spec を真実の源とする通常の SDD に戻す。
- **Rationale**: 本機能自体が「実装 ↔ spec の乖離検出」であるため、実装が先行した特殊ケースである。逆算記述の経緯は D-001（Specification-Driven）の例外プロセスに従って記録する。
- **Rejected alternatives**: 実装より先行して仕様を書く — 本機能はすでに稼働していたため選択できなかった。

## 2026-09-10 比較基準を spec 第一級とし、設計ドラフトは存在時のみ補助にする

- **Decision**: 比較基準のドキュメントは spec を第一級とし、`task/{ticket-number}/design-draft.md` は存在する場合のみ補助入力として扱う。
- **Rationale**: Design Doc は実装完了後に削除される一時ドラフトになったため、恒久的な比較基準にできない。spec は永続ドキュメントであり真実の源として安定している。
- **Rejected alternatives**: 永続 design を比較基準にする — v5 で技術設計が永続文書でなくなったため却下。

## 2026-09-10 設計ドラフトの不在を正常系として扱う

- **Decision**: 設計ドラフトが存在しない場合を WARNING やエラーではなく正常系（ログのみ、警告なし）として扱う。
- **Rationale**: 実装完了後はドラフト不在が通常の状態であり、警告を出すと恒常的なノイズになる。
- **Rejected alternatives**: WARNING / エラーとして報告する — 通常状態に対する恒常的なノイズになるため却下。

## 2026-09-10 リテラル値の権威的定義を spec の Schema Registry に置く

- **Decision**: リテラル値の権威的定義は spec の Schema Registry を優先し、そこに無い場合のみ本文から抽出する。
- **Rationale**: 値の真実の源を spec に一元化することでトレーサビリティを確保できる。
- **Rejected alternatives**: 設計ドラフト本文のみを参照する — 一時ドラフトに値の真実の源を置くことになるため却下。

## 2026-09-10 値比較は等価表現を正規化してから行う

- **Decision**: リテラル値の比較を表記そのままでは行わず、等価表現を正規化してから比較する（例: `70%` ↔ `0.7`、`15s` ↔ `15000ms`）。報告は各層の元表記で行う。
- **Rationale**: 表記差による誤検出を防ぐため。報告を元表記で行うことで、正規化が利用者から見えなくなることも避けられる。
- **Rejected alternatives**: 表記そのままで比較する — 等価な値を乖離として誤検出するため却下。
