---
id: "adr-distribution"
title: "配布・運用 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-distribution"]
tags: ["marketplace", "versioning", "i18n", "ci", "cross-platform"]
category: "distribution"
---

# 配布・運用 決定ログ

## 2026-07-24 バージョンをマニフェストに一元化する

- **Decision**: バージョンを plugin.json を単一ソースとして管理し、plugin.json / marketplace.json / タグの 3 者一致を CI（release.yml）で検証する。
- **Rationale**: 各コンポーネントに分散記載すると更新漏れで不整合を招くため。DC_001（バージョンの単一ソース制約）が一元化を要求する。
- **Rejected alternatives**: 各コンポーネントにバージョンを記載する — 更新漏れによる不整合を機械検知できないため却下。

## 2026-07-24 リリースを prepare + 手動タグ + release の 2 段構えにする

- **Decision**: リリースを prepare-release.yml（PR 自動化）→ 人手によるタグ打ち → release.yml（公開リポ同期・Release 作成）の 2 段構えで実行する。
- **Rationale**: `GITHUB_TOKEN` で push したタグは GitHub Actions のワークフローをトリガーしないというプラットフォーム制約があり、全自動化が成立しない。タグ打ちを人手に残すことで誤配布も防げる（FR-002）。
- **Rejected alternatives**: タグ push で全自動リリース — 上記のトリガー制約により release.yml が起動しないため却下。

## 2026-07-24 develop → main の統合はマージコミットで行う

- **Decision**: develop → main の統合を squash merge ではなくマージコミットで行う。
- **Rationale**: 長命ブランチ同士の統合であり、main と develop に履歴を共有させないと以後の分岐・back-merge が必要になるため。
- **Rejected alternatives**: squash merge — 履歴は簡潔になるが main と develop の履歴が乖離し、統合ごとに分岐が生じるため却下。

## 2026-07-24 検証ロジックを CI 専用ではなく共用シェルスクリプトに置く

- **Decision**: 構造検証・リントを `scripts/*.sh`（validate-marketplace.sh / plugin-lint.sh）として実装し、CI とローカルで同一のスクリプトを実行する。
- **Rationale**: CI 専用の inline 実装では開発者がローカルで事前に品質確認できず、CI でしか失敗が判明しない（FR-004）。
- **Rejected alternatives**: CI ワークフロー内に inline で検証を書く — ローカル実行手段が失われるため却下。

## 2026-07-24 配布先を開発リポと公開リポに分離する

- **Decision**: 開発は dev リポで行い、release.yml が rsync で公開リポ（ToshikiImagawa/ai-sdd-workflow）へ配布物のみを同期する。
- **Rationale**: 開発履歴・内部資材と配布物を分離し、公開リポには利用者が必要とするものだけを置くため。
- **Rejected alternatives**: dev リポで直接公開する — 内部資材と開発履歴が配布物に混ざるため却下。

## 2026-07-24 クロスプラットフォーム検証を 2 OS マトリクスで行う

- **Decision**: shellcheck ジョブと test ジョブを `[ubuntu-latest, macos-latest]` のマトリクスで実行する。
- **Rationale**: 単一 OS の実行では OS 依存の混入を検知できず、移植性の退行（NFR-001）が配布まで残るため。
- **Rejected alternatives**: 単一 OS での実行 — OS 依存の退行を検知できないため却下。Windows ランナーの追加 — ネイティブサポート要求が固まっていない段階では Linux/macOS で担保するに留める。

## 2026-07-28 plugin.json は agents のみを宣言し skills / hooks は宣言しない

- **Decision**: plugin.json のコンポーネントパスフィールドは `agents` のみを宣言し、`skills` / `hooks` は宣言しない。あわせて `agents/` にはエージェント定義のみを置き、サポートファイルは `shared/` に集約する。
- **Rationale**: Claude Code のコンポーネントパスフィールドは挙動が 3 種類に分かれる（`agents` は既定走査を**置換**、`skills` は**加算**、`hooks` は既定パスを**補完**）ため、一律登録は成立しない。`agents` は配列に載せたファイルのみ読み込まれるので宣言必須、`skills` は標準パスが常に走査されるので宣言が冗長、`hooks` は標準パスを明示すると同一ファイルの二重ロードとなりローダーが拒否する（T-002 v2.0.0）。`agents/` にサポートファイルを置けないのは `claude plugin validate --strict` がマニフェストを無視して `agents/**` を再帰走査し、それらをエージェント定義として扱うためである。
- **Rejected alternatives**: 全コンポーネントを一律に plugin.json へ登録する — `hooks` の二重ロードでプラグインのロード自体が失敗するため却下。

## 2026-07-28 マニフェスト・front matter の衛生検査を CLI 非依存で CI に持つ

- **Decision**: `claude plugin validate --strict` はローカル手動検証に留め、CI では plugin-lint.sh のマニフェスト衛生検査・front matter 衛生検査で同等の不変条件を担保する。
- **Rationale**: 宣言しても警告なく無視される front matter キーの誤用（サブエージェントの `allowed-tools`、スキルの `agent:` へのモデル名、`context: fork` を伴わない `agent:`、hooks.json の未クォート `${CLAUDE_PLUGIN_ROOT}`）は人手では気付けない。一方で公式バリデータを CI に入れると npm/node 依存をリポジトリに持ち込むことになる。
- **Rejected alternatives**: `claude plugin validate --strict` を CI ジョブにする — 本リポジトリが避けている npm/node 依存を持ち込むため却下。

## 2026-07-28 スキルの allowed-tools からベアな Write / Edit / Bash を排除する

- **Decision**: スキルの `allowed-tools` にベアな `Write` / `Edit` / `Bash` を書かず、書き込みは `Edit(.sdd/**)` 等のパス指定子、シェルは `Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/<script>.py" *)` の形で同梱スクリプトに限定する。plugin-lint.sh の Check 5.4 がこれを機械検知する。
- **Rationale**: `allowed-tools` は「許可を尋ねずに使えるツール」の**事前承認**であり制限リストではない。ベアな `Write` / `Edit` は任意パスへの書き込みを、ベアな `Bash` は任意コマンド実行を無確認で通してしまうが、記述の見た目からは危険度が読み取れない。スコープを絞りすぎても利用者に権限確認が出るだけで機能は失われない（fail-safe）。なお `Write(<path>)` はファイル権限チェックにマッチせず、`Edit(<path>)` ルールが Write を含む全ファイル編集ツールをカバーする。
- **Rejected alternatives**: None considered

## 2026-07-28 CHANGELOG を Keep a Changelog 準拠で日英併記する

- **Decision**: CHANGELOG.md / CHANGELOG.ja.md を Keep a Changelog 準拠のバージョン節構成で日英併記し、release.yml が該当バージョン節を抽出してリリースノートにする。
- **Rationale**: リリースノートを機械抽出するにはバージョンごとの節構成が必要であり、多言語対応の一貫性（B-002）が日英併記を要求する。
- **Rejected alternatives**: None considered
