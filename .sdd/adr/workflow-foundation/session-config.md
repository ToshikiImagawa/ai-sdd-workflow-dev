---
id: "adr-workflow-foundation-session-config"
title: "セッション設定初期化 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-07-24"
sdd-version: "5.0.0"
depends-on: ["spec-workflow-foundation-session-config"]
tags: ["session-config", "hooks", "environment", "index"]
category: "workflow-foundation"
---

# セッション設定初期化 決定ログ

## 2026-07-24 起動方式を SessionStart フックにする

- **Decision**: セッション設定の初期化をスキルの手動呼び出しではなく SessionStart フックで行う。
- **Rationale**: 一貫した設定は全コンポーネントの前提であり、セッション開始ごとに自動・決定的に初期化する必要がある（A-002）。
- **Rejected alternatives**: スキルの手動呼び出しにする — 初期化漏れが全コンポーネントの前提を崩すため却下。

## 2026-07-24 設定不正時は既定値へフォールバックする

- **Decision**: 設定ファイルが不正な場合はエラー中断せず、警告のうえ既定値へフォールバックして継続する。
- **Rationale**: 設定不正でセッションを止めると可用性を損なう（NFR-001 / DC_002）。
- **Rejected alternatives**: エラーで中断する — 設定の軽微な不備でセッションが起動しなくなるため却下。

## 2026-07-24 env export を prefix 単位で旧値置換する

- **Decision**: `CLAUDE_ENV_FILE` への export 書き出しを追記のみとせず、`rewrite_exports` で prefix 単位に旧値を置換する。
- **Rationale**: 追記のみだと再実行で `SDD_*` の値が陳腐化・重複するため、最新値へ更新する必要がある（NFR-003）。
- **Rejected alternatives**: 追記のみにする — 再実行で値が陳腐化・重複するため却下。

## 2026-07-24 index の制御値を真偽値のみにする

- **Decision**: インデックス有効化の設定値を文字列 on/off ではなく真偽値のみとし、非真偽値は警告 + 既定値フォールバックとする。
- **Rationale**: 型を真偽値に統一することで曖昧さを排除でき、フォールバックにより誤設定にも耐えられる。
- **Rejected alternatives**: 文字列 on/off を許容する — 表記の揺れによる曖昧さが残るため却下。

## 2026-07-24 インデックス構築を Python 標準ライブラリで実装する

- **Decision**: インデックス構築を jq / sqlite3 等の外部 CLI ではなく Python 標準ライブラリ（`sqlite3` モジュール）で実装する。
- **Rationale**: `sqlite3` モジュールは標準で同梱されており、OS 固有 CLI に依存しないため移植性を確保できる（NFR-002）。
- **Rejected alternatives**: 外部 CLI（jq / sqlite3 コマンド）を使う — OS 固有 CLI 依存で移植性を損なうため却下。

## 2026-07-24 ルート解決を CLAUDE_PROJECT_DIR → git → CWD のフォールバック連鎖にする

- **Decision**: プロジェクトルートの解決を CWD 固定とせず、`CLAUDE_PROJECT_DIR` → git ルート → CWD の順のフォールバック連鎖で行う。
- **Rationale**: フック実行時の CWD は不定であるため、環境変数と git ルートを先に試すことで頑健に解決できる。
- **Rejected alternatives**: CWD 固定にする — フック実行時の CWD が不定であり誤ったルートを解決するため却下。

## 2026-07-24 `.sdd-config.json` に `directories.adr` を明示する

- **Decision**: `.sdd-config.json` の `directories` に `adr` を明示的に記載する。
- **Rationale**: `adr_dir` は既定値にフォールバックするため明示しなくても動作するが、`requirement` / `specification` / `task` は既定値と同値でも `directories` に明示されている。`adr` のみ省略すると設定ファイルの表記方針が一貫しなくなる。
- **Rejected alternatives**: 既定値 `"adr"` に委ねて明示しない — 他のディレクトリ指定との表記方針が一貫しなくなるため却下。
