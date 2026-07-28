# テストと検証

- プラグインJSON構文チェック: `cat plugins/*/.claude-plugin/*.json | jq .`
- Python ユニットテスト: `python3 -m pytest tests/ -v`（要 `pip install pytest`。CI の `test` ジョブでも実行）。フックスクリプト（session-start / pre-tool-use / post-tool-use / user-prompt-submit / hook_common）と共有モジュール（fm_parser / naming / doc_walker / env_export）、sdd_index、skill ヘルパーをカバー。新規テストは `tests/` に置けば `pytest tests/` が自動収集する（CI 配線の追加は不要）
- sdd-init 通しE2E: `bash scripts/test-e2e-sdd-init.sh`（空プロジェクトで session-start → init-structure → update-claude-md を連鎖検証。en/ja テンプレート描画・custom root を含む。要 `python3` / `jq`。CI の `test` ジョブでも実行）
- skill ヘルパースクリプト回帰: `bash scripts/test-skill-scripts.sh`（find-design-docs.py / validate-files.py が custom root でキャッシュを設定 root 配下に生成するか検証。CI の `test` ジョブでも実行）
- プラグイン構造 Lint: CI の `plugin-lint` ジョブは2ステップで、`bash scripts/plugin-lint.sh`（構造・マニフェスト・front matter キー）と `python3 .claude/skills/plugin-lint/scripts/plugin_lint.py`（スキル `allowed-tools` のツール名妥当性・重複）を両方実行する。ローカルでも両方を流して exit 0 を確認する。2系統の役割分担と同期義務は `.claude/rules/scripts.md` を参照
- 公式バリデータ（ローカル手動）: `claude plugin validate ./plugins/sdd-workflow --strict` で Claude Code CLI 自身の検証を通す。認証不要でオフライン実行できるが、CI には**入れていない**（このリポジトリの CI は npm/node 依存を持たないため）。CI では `plugin-lint.sh` の Check 4.2（`agents/` にサブディレクトリを置かない・`agents/*.md` は front matter を持つ）が同等の不変条件を担保している
- Markdownリンクの整合性: 各ドキュメント内の相対リンクが有効か確認
- **IMPORTANT**: 新規エージェント追加時は `plugin.json` の `agents` 配列への登録を忘れずに（この配列はデフォルトの `agents/` スキャンを置き換えるため、未登録のエージェントはロードされない）。スキルは `skills/` が常にスキャンされるので登録不要（CONSTITUTION T-002 v2.0.0）
- プラグインデバッグ: `claude --debug` でプラグインの読み込み、フック実行、エージェント呼び出しの詳細ログを確認
- ローカルテスト: `claude --plugin-dir ./plugins/sdd-workflow` でローカルのプラグインを直接テスト
