---
id: "adr-task-implementation-implement"
title: "TDD 実装 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-task-implementation-implement"]
tags: ["tdd", "implementation", "checklist"]
category: "task-implementation"
---

# TDD 実装 決定ログ

## 2026-07-24 テスト先行を段階順序として強制する

- **Decision**: Tests 段階を Core 段階より前に固定し、段階順序としてテスト先行を強制する。
- **Rationale**: 推奨に留めるとテストのない実装へ進行し得る。順序を段階として固定することで構造的に防げる（DC_001）。
- **Rejected alternatives**: テスト先行を推奨に留める — テストのない実装への進行を防げないため却下。

## 2026-07-24 進捗管理に TaskList を使う

- **Decision**: 実装の進捗管理に TaskList を用い、利用できない環境では Markdown で代替する。
- **Rationale**: 5 段階の複数ステップを可視化し、ユーザーが進捗を追跡できるようにするため（NFR-003）。
- **Rejected alternatives**: Markdown のみで管理する — 進捗の可視性が劣るため既定としては却下（フォールバックとしては採用）。

## 2026-07-24 Bash を事前承認せず都度ユーザー確認を挟む

- **Decision**: Bash を `allowed-tools` で事前承認せず、禁止もしない（都度ユーザー確認を経て実行する）。
- **Rationale**: テスト実行・型チェック等の検証コマンドに Bash は必要だが、実行対象がプロジェクト任意のコマンドであるため事前承認できない。
- **Rejected alternatives**: Bash を禁止する — 検証コマンドを実行できなくなるため却下。Bash を事前承認する — 任意コマンドを無確認で実行できてしまうため却下。

## 2026-07-24 乖離検出を段階境界で行う

- **Decision**: 実装完了後のみではなく、各段階の境界で check-spec の実行を推奨する。
- **Rationale**: 早期に乖離を検知することで手戻りを抑えられる（FR-008 / B-001）。
- **Rejected alternatives**: 完了後のみ検出する — 乖離の発見が遅れ手戻りが大きくなるため却下。

## 2026-07-24 continue / phase-skip / dry-run の複数実行モードを提供する

- **Decision**: 実行モードとして continue / phase-skip / dry-run を提供する。
- **Rationale**: 中断再開・特定段階からの着手・非破壊シミュレーションという実運用上のニーズに対応するため。
- **Rejected alternatives**: 単一モードのみ提供する — 中断再開や部分実行の実運用ニーズに応えられないため却下。

## 2026-09-02 設計ドラフトの参照パスをチケット単位の固定パスにする

- **Decision**: 参照する設計ドラフトを `task/{ticket}/design-draft.md` のチケット単位固定パスとする。
- **Rationale**: generate-spec / task-breakdown と同一のパスを参照することで、順方向フローで参照先が食い違わない。
- **Rejected alternatives**: 機能単位の `specification/*_design.md` を参照する — v5 の出力先と食い違うため却下。

## 2026-09-02 抽象仕様書の前提判定をサフィックス有無の両方で充足させる

- **Decision**: 前提条件チェックにおける抽象仕様書の存在判定を、`{feature}.md` と `{feature}_spec.md` のいずれかで充足とする。
- **Rationale**: `specification/` は単一種別ディレクトリとなりサフィックスが任意になったため、片方だけを前提にすると前提条件チェックが通らない。
- **Rejected alternatives**: `_spec` サフィックスを必須とする — サフィックス任意の新方針の下で正常な文書を不在と判定するため却下。
