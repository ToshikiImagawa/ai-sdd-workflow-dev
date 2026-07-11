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
| `plugin-lint.sh`          | `.claude/skills/plugin-lint/SKILL.md` の検査内容を実装。プロンプトMD内の不適切なコードブロックやファイル命名規則を検証 | `plugin-lint` |
| `test-session-start.sh`   | `plugins/sdd-workflow/scripts/session-start.py` のゴールデンファイル回帰テスト     | `test`        |
| `test-hook-scripts.sh`    | `plugins/sdd-workflow/scripts/` のフックスクリプト（pre-tool-use / post-tool-use / user-prompt-submit）の回帰テスト | `test`        |
| `test-e2e-sdd-init.sh`    | 空プロジェクトでの sdd-init 通しE2E（session-start → init-structure → update-claude-md）。CLAUDE.md 最小化・`.claude/rules/` 生成・レガシー掃除・冪等性・en/ja テンプレート描画・custom root を検証 | `test`        |
| `test-skill-scripts.sh`   | skill ヘルパースクリプト（check-spec の `find-design-docs.sh` / constitution の `validate-files.sh`）が custom root でキャッシュ・エクスポートを設定 root 配下に生成するか検証 | `test`        |

## 実装・修正時の注意

- POSIX準拠（macOS bash 3.2 / dash）を維持する。bash専用構文を使わない
- `shellcheck` ジョブが全 `.sh` ファイルを `-S warning -e SC1091` でチェックする。追加・修正時はローカルで `shellcheck -S warning -e SC1091 scripts/*.sh` を実行して確認する
- スクリプトパス・実行コマンドを変更する場合は `.github/workflows/ci.yml` の対応する `run:` も同時に更新する
- `plugin-lint.sh` の検証ロジックを変更する場合は `.claude/skills/plugin-lint/SKILL.md` との整合性も確認する
- `validate-marketplace.sh` はプラグイン数・バージョンをハードコードしていない（`marketplace.json` を動的に読む）ため、プラグイン追加時のスクリプト修正は不要
