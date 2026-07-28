---
name: plugin-lint
description: "Lint check for AI-SDD plugin prompt files and support file structure. Detects code blocks in prompt Markdown and validates naming conventions."
version: 3.0.0
license: MIT
user-invocable: true
argument-hint: "[none]"
allowed-tools: Bash, Read
---

# Plugin Lint - プラグイン構造品質チェック

プラグインのプロンプトMarkdownファイルとサポートファイル構造をlintチェックし、問題をレポートする。自動修正は行わない。

検出ロジックはすべて Python スクリプト（`scripts/plugin_lint.py`）に実装されている。このスキルの役割は、スクリプトの実行と結果の整形レポートのみ。

## Input

$ARGUMENTS

引数なしで全体チェックを実行する。

### Input Examples

/plugin-lint

## Check Items

スクリプトが以下をチェックする（詳細は `scripts/plugin_lint.py` を参照）:

| Check ID | 内容 |
|:---|:---|
| 1 | プロンプトMarkdown（`plugins/sdd-workflow/agents/*.md`, `skills/*/SKILL.md`）内のコードブロック検出。開始フェンスのみを1件として数える |
| 2.1 | スキルディレクトリ直下のエントリが `SKILL.md`, `README.md`, `templates`, `examples`, `references`, `scripts` のいずれかであること |
| 2.2 | サポートファイル名が snake_case（`^[a-z0-9_]+\.[a-z]+$`）であること |
| 2.3 | `templates/` に `en/` と `ja/` の両方が存在すること |
| 2.4 | `templates/en/` と `templates/ja/` の直下ファイル名セットが一致すること |
| 2.5 | サポートファイルの拡張子が `.md` であること |
| 3.1 | スキル `SKILL.md` の `allowed-tools` に列挙されたツール名が実在すること。`Edit(.sdd/**)` や `Bash(python3 "${CLAUDE_PLUGIN_ROOT}/..." *)` のような指定子付き宣言は**ツール名部分（`(` の手前）だけ**を既知名と照合する。あわせて指定子の括弧が閉じていないケース（指定子にカンマを含めた場合など）も検出する |
| 3.2 | `allowed-tools` にツール名の重複がないこと |

**2.2 / 2.5 の対象範囲**: 各スキルの `templates/` `examples/` `references/` 配下（再帰）と
`plugins/sdd-workflow/shared/references/` 配下。`scripts/` は実行コードなので両チェックの対象外。

**3.1 は指定子を許容する**: `allowed-tools` は「許可を尋ねずに使えるツール」の事前承認であり、permissions と同じ
`ツール名(指定子)` 構文で範囲を絞れる。したがって指定子付き宣言は未知ツールとして扱わない。
一方、ベアな `Write` / `Edit` / `Bash`（スコープ無しの事前承認）の検出はシェル版 `scripts/plugin-lint.sh` の
Check 5.4 が担当し、本スクリプトでは検出しない。

**採番は本スクリプト固有**: 上記 Check ID は `scripts/plugin_lint.py` の採番であり、CI の
`plugin-lint` ジョブが併走させるシェル版 `scripts/plugin-lint.sh` とは**別体系**。
たとえばシェル版の "Check 3" は `${SDD_*}` パストークン健全性で、本スクリプトの "3.1 / 3.2"
（`allowed-tools` 検証）とは別物。シェル版にしかない検査（`${SDD_*}` トークン、`plugin.json`
マニフェスト衛生、front matter キー衛生）は本スクリプトでは検出されない。

## Processing Flow

### Step 1: Run Lint Script

Bash でスクリプトを実行する:

    python3 "$(git rev-parse --show-toplevel)/.claude/skills/plugin-lint/scripts/plugin_lint.py"

- 終了コード 0: 問題なし
- 終了コード 1: 問題あり（stdout の JSON に findings が含まれる）
- 終了コード 2: 実行エラー（stderr を確認して報告する）

出力 JSON の構造: `{"total": n, "summary_by_check": {"<check_id>": n}, "findings": [{"check_id", "file", "line", "message", ...}]}`

findings が多い場合は出力をファイルにリダイレクトし、Read で読み取る。

### Step 2: Report Generation

JSON 結果を `templates/lint_report.md` テンプレートの形式で整形して報告する。

- 各チェック項目のステータス（✅ パス / ⚠️ 警告）と件数を summary_by_check から埋める
- Check 1 の findings には推奨事項（`templates/`, `examples/`, `references/` への分離）を添える
- 件数が多い場合はファイル単位で集約して報告してよい

## Notes

- このスキルは **検出とレポートのみ** を行い、自動修正は行わない
- コードブロック検出は誤検知の可能性がある（意図的に含めている場合）ため、開発者の判断に委ねる
- チェックロジックの変更は `scripts/plugin_lint.py` を編集する（SKILL.md ではなく）
