---
id: "adr-workflow-foundation-cross-platform-portability"
title: "クロスプラットフォーム移植性 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-14"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-workflow-foundation-cross-platform-portability"]
tags: ["portability", "cross-platform", "python", "scripts", "ci"]
category: "workflow-foundation"
---

# クロスプラットフォーム移植性 決定ログ

## 2026-07-14 スクリプトの統一言語を Python 標準ライブラリにする

- **Decision**: スクリプト・フックの実装言語を Python 標準ライブラリに統一する。
- **Rationale**: フックは既に Python で cross-platform に動作している。OS ごとに Bash + PowerShell の二本立てにすると二重ツールチェーン化を招き、CI に PowerShell がないためカバレッジも欠落する。Bash + 外部 CLI は OS 固有 CLI 依存で移植性を損なう（#17）。
- **Rejected alternatives**: Bash + 外部 CLI — OS 固有 CLI 依存で移植性を損なうため却下。OS ごとに Bash + PowerShell の二本立て — 二重ツールチェーン化と CI カバレッジ欠如を招くため却下。

## 2026-07-14 パス処理を pathlib 基本とする

- **Decision**: パス処理は `pathlib` を基本とし、既存フックの `os.path` は許容する。
- **Rationale**: `pathlib` は OS 非依存で可読性が高い。`os.path` も OS 非依存であるため既存フックをただちに書き換える必要はなく、統一は #32 で継続する。
- **Rejected alternatives**: 文字列連結でパスを組む — OS 依存のセパレータ問題を招くため却下。

## 2026-07-14 移植性の検証を複数 OS マトリクスで行う

- **Decision**: 移植性の検証を単一 OS CI ではなく ubuntu / macos の複数 OS マトリクスで行う。
- **Rationale**: 単一 OS では OS 依存の混入を検知できず、両 OS で実行することで退行を検知できる。
- **Rejected alternatives**: 単一 OS CI — OS 依存の混入を検知できないため却下。

## 2026-07-14 本機能のスコープを実現済みの移植性に限定する

- **Decision**: 本機能の仕様範囲を、Windows ネイティブ完全対応までは含めず、実現済みの移植性に限定する。
- **Rationale**: #10 のネイティブサポートは範囲が未確定であり、未確定範囲を仕様に含めると陳腐化するため（FR-004）。
- **Rejected alternatives**: Windows ネイティブ完全対応まで仕様化する — 範囲未確定のまま書くと陳腐化するため却下。

## 2026-07-28 外部プロセス呼び出しを git のみ許容する

- **Decision**: subprocess による外部プロセス呼び出しを原則禁止としつつ、`git` に限り許容する。プロジェクトルート検出は `$CLAUDE_PROJECT_DIR` → `git rev-parse --show-toplevel` → CWD の順でフォールバックする。
- **Rationale**: `git` は Windows を含めて広く利用可能な準標準ツールであり、プロジェクトルート検出という用途では代替手段が乏しい。一方 `find` / `sed` / `jq` / `grep` / `awk` 等の OS 固有 CLI は挙動差が大きいため引き続き禁止する。
- **Rejected alternatives**: subprocess を一切禁止する — プロジェクトルート検出の信頼できる手段が失われるため却下。
