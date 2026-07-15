# テストと検証

- プラグインJSON構文チェック: `cat plugins/*/.claude-plugin/*.json | jq .`
- Python ユニットテスト: `python3 -m pytest tests/ -v`（要 `pip install pytest`。CI の `test` ジョブでも実行）。フックスクリプト（session-start / pre-tool-use / post-tool-use / user-prompt-submit / hook_common）と共有モジュール（fm_parser / naming / doc_walker / env_export）、sdd_index、skill ヘルパーをカバー。新規テストは `tests/` に置けば `pytest tests/` が自動収集する（CI 配線の追加は不要）
- sdd-init 通しE2E: `bash scripts/test-e2e-sdd-init.sh`（空プロジェクトで session-start → init-structure → update-claude-md を連鎖検証。en/ja テンプレート描画・custom root を含む。要 `python3` / `jq`。CI の `test` ジョブでも実行）
- skill ヘルパースクリプト回帰: `bash scripts/test-skill-scripts.sh`（find-design-docs.py / validate-files.py が custom root でキャッシュを設定 root 配下に生成するか検証。CI の `test` ジョブでも実行）
- Markdownリンクの整合性: 各ドキュメント内の相対リンクが有効か確認
- **IMPORTANT**: 新規エージェント/スキル追加時は `plugin.json` への登録を忘れずに
- プラグインデバッグ: `claude --debug` でプラグインの読み込み、フック実行、エージェント呼び出しの詳細ログを確認
- ローカルテスト: `claude --plugin-dir ./plugins/sdd-workflow` でローカルのプラグインを直接テスト
