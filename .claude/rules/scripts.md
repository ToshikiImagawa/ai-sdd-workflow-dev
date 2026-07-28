---
paths:
  - "scripts/**"
---

# scripts/ 作業ガイド

このディレクトリには、マーケットプレイス・プラグインの検証、Lint、テスト用シェルスクリプトが含まれます。
すべて GitHub Actions（`.github/workflows/ci.yml`）から同じコマンドで実行されるため、**CIジョブとの対応関係を崩さないこと**。

| スクリプト                     | 役割                                                                 | CIジョブ      |
|:--------------------------|:-------------------------------------------------------------------|:------------|
| `validate-marketplace.sh` | `marketplace.json` / `plugin.json` のJSON構文・必須フィールド・バージョン整合性を検証     | `validate`    |
| `plugin-lint.sh`          | プラグイン構造の Lint。プロンプトMD内のコードブロック検出（Check 1・警告のみ）、サポートファイル構造（Check 2）、`${SDD_*}` パストークン健全性（Check 3）、マニフェスト衛生と `agents/` レイアウト（Check 4 / 4.2）、front matter キー衛生と `allowed-tools` の事前承認スコープ（Check 5 / 5.4）を検証 | `plugin-lint`（1/2ステップ） |
| `test-session-start.sh`   | `plugins/sdd-workflow/scripts/session-start.py` のゴールデンファイル回帰テスト     | `test`        |
| `test-hook-scripts.sh`    | `plugins/sdd-workflow/scripts/` のフックスクリプト（pre-tool-use / post-tool-use / user-prompt-submit）の回帰テスト | `test`        |
| `test-e2e-sdd-init.sh`    | 空プロジェクトでの sdd-init 通しE2E（session-start → init-structure → update-claude-md）。CLAUDE.md 最小化・`.claude/rules/` 生成・レガシー掃除・冪等性・en/ja テンプレート描画・custom root を検証 | `test`        |
| `test-skill-scripts.sh`   | skill ヘルパースクリプト（check-spec の `find-design-docs.py` / constitution の `validate-files.py`）が custom root でキャッシュ・エクスポートを設定 root 配下に生成するか検証 | `test`        |

## plugin-lint の2系統

`plugin-lint` ジョブは**2ステップ**で、独立した2つの Linter を順に実行する。両者は検査項目が重複せず、
**どちらか一方だけでは検査が欠落する**。

| ステップ | 実装                                              | 検査範囲                                                                          |
|:-----|:------------------------------------------------|:------------------------------------------------------------------------------|
| 1    | `scripts/plugin-lint.sh`                        | 構造・マニフェスト・front matter。Check 1（コードブロック）/ 2（サポートファイル構造・`shared/` を含む）/ 3（`${SDD_*}` トークンと `.sdd/` ハードコード）/ 4（`plugin.json`）/ 4.2（`agents/` にサブディレクトリを置かない・`agents/*.md` は front matter を持つ）/ 5（front matter キー衛生: 5.1 エージェントの `allowed-tools` 誤用 / 5.2 `agent:` 誤用 / 5.3 `${CLAUDE_PLUGIN_ROOT}` の未クォート / 5.4 スキルの `allowed-tools` にベアな `Write` / `Edit` / `Bash`） |
| 2    | `.claude/skills/plugin-lint/scripts/plugin_lint.py` | スキル `SKILL.md` の `allowed-tools` に列挙されたツール名の妥当性（指定子付き宣言はツール名部分を照合し、閉じていない括弧も検出）と重複（シェル版に無い）。加えて Check 1 / 2 相当も JSON で出力する |

**採番は別体系**である点に注意する。シェル版の "Check 3" は `${SDD_*}` パストークン、Python 版の
"3.1 / 3.2" は `allowed-tools` 検証で、同じ番号でも別物。

**Check 5.4 の趣旨**: スキルの `allowed-tools` は「許可を尋ねずに使えるツール」の**事前承認**であり制限リストではない。
ベアな `Write` / `Edit` は任意のパスへの書き込みを、ベアな `Bash` は任意のコマンド実行を無確認で通してしまうため、
`Edit(.sdd/**)` / `Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/<script>.py" *)` のように指定子で絞る。
書き込みの限定は `Edit(<path>)` で行う（`Write(<path>)` はファイル権限チェックにマッチせず、`Edit(<path>)` ルールが
Write を含む全ファイル編集ツールをカバーする）。

### 変更時の同期義務

- シェル版だけにある検査（Check 3〜5）を変更した場合、同期先は無い。`scripts/plugin-lint.sh` が正典
- Python 版の検出ロジックを変更した場合、正典は `.claude/skills/plugin-lint/scripts/plugin_lint.py` であり、
  `.claude/skills/plugin-lint/SKILL.md` の「Check Items」表はその**説明**なので追随させる
- 両版が共通で見ている項目（コードブロック検出、サポートファイル構造）を変更する場合は、
  **シェル版と Python 版の双方**を更新する。片方だけ直すと CI のステップ間で判定が食い違う
- `.claude/skills/plugin-lint/` と `.agents/skills/plugin-lint/` は同内容のミラー。片方を変更したら他方も揃える

## 実装・修正時の注意

- POSIX準拠（macOS bash 3.2 / dash）を維持する。bash専用構文を使わない
- `shellcheck` ジョブが全 `.sh` ファイルを `-S warning -e SC1091` でチェックする。対象は `scripts/` 配下だけでなく
  `.claude/tests/harness/` や各スキルの `scripts/` も含むため、ローカル確認は CI と同じコマンドを使う:
  `find . -name "*.sh" -type f -print0 | xargs -0 shellcheck -S warning -e SC1091`
- スクリプトパス・実行コマンドを変更する場合は `.github/workflows/ci.yml` の対応する `run:` も同時に更新する
- `plugin-lint` の検証ロジックを変更する場合は上記「変更時の同期義務」に従う
- `validate-marketplace.sh` はプラグイン数・バージョンをハードコードしていない（`marketplace.json` を動的に読む）ため、プラグイン追加時のスクリプト修正は不要
