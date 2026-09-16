---
id: "adr-task-implementation-task-cleanup"
title: "タスククリーンアップ 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-task-implementation-task-cleanup"]
tags: ["task-cleanup", "knowledge-persistence"]
category: "task-implementation"
---

# タスククリーンアップ 決定ログ

## 2026-07-24 実行モデルを haiku にする

- **Decision**: task-cleanup のモデルを `haiku` とする。
- **Rationale**: 知見の選別・統合は判断を要するが定型度が高く、軽量モデルでコスト効率を優先できる。
- **Rejected alternatives**: 既定モデルを使う — 定型度の高い処理に対して過剰なコストとなるため却下。

## 2026-07-24 削除を `git rm` で行う

- **Decision**: task ディレクトリの削除を `rm` ではなく `git rm`（ディレクトリは `-r`）で行う。
- **Rationale**: Git 管理下で削除することで履歴追跡と取り消しが可能になる。
- **Rejected alternatives**: `rm` で削除する — 履歴追跡・取り消しができないため却下。

## 2026-07-24 統合 → front matter 更新 → 削除の順序を固定する

- **Decision**: 処理順序を「知見の統合 → front matter 更新 → 削除」に固定する。
- **Rationale**: 統合前削除の禁止（DC_002 / D-003）をプロセスの順序として構造的に担保するため。
- **Rejected alternatives**: 順序を固定しない — 統合前に削除して知見が失われるリスクが残るため却下。

## 2026-07-24 統合先が無い場合も新規に ADR を作成する

- **Decision**: 統合先の決定ログが存在しない場合も、常に新規に `adr/{feature}.md`（サフィックス無し）を作成して統合する。
- **Rationale**: 孤立した ADR の乱造を避けるより、根拠ある知見を確実に永続化することを優先する。
- **Rejected alternatives**: 統合先が無い場合は統合をスキップする — 根拠ある知見が削除とともに失われるため却下。

## 2026-07-24 引数なし実行時は範囲確認でユーザー承認を得る

- **Decision**: 引数なしで実行された場合は即実行せず、削除範囲を提示してユーザーの承認を得る。
- **Rationale**: `task/` 全体を削除してしまう誤操作を防ぐため（NFR-001）。
- **Rejected alternatives**: 即実行する — `task/` 全体削除の誤操作を防げないため却下。

## 2026-07-24 移行の履歴表記を残さない

- **Decision**: 知見の統合時に、移行元や移行日時といった履歴表記を残さない。
- **Rationale**: 統合先の文書を成果物として簡潔に保ち、移行の痕跡でノイズを増やさないため（NFR-003）。
- **Rejected alternatives**: 移行履歴を残す — 成果物にノイズが増えるため却下。
