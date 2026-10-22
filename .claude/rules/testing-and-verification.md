# テストと検証

- プラグインJSON構文チェック: `cat plugins/*/.claude-plugin/*.json | jq .`
- Python ユニットテスト: `python3 -m pytest tests/ -v`（要 `pip install pytest`。CI の `test` ジョブでも実行）。フックスクリプト（session-start / pre-tool-use / post-tool-use / user-prompt-submit / hook_common）と共有モジュール（fm_parser / naming / doc_walker / env_export）、sdd_index、skill ヘルパーをカバー。新規テストは `tests/` に置けば `pytest tests/` が自動収集する（CI 配線の追加は不要）
- 法則 vs 実装の差分テスト: `python3 -m pytest tests/laws/ -q`。`.sdd/laws/**/LAWS.bend` の法則（点命題）を参照モデルではなく Python 実装に対して assert する（laws-drafting_spec FR-014。bend 不要。`pytest tests/` に含まれる）。各テスト直前の `# source:` 行は `bash scripts/check-laws-tests.sh`（全ファイル一括。CI の `test` ジョブでも実行）または `python3 plugins/sdd-workflow/skills/draft-laws/scripts/draft_laws.py check --tests tests/laws/test_<feature>.py --spec .sdd/specification/<feature>_spec.md`（単体）で spec の節ハッシュと照合する（spec を変えたら節ハッシュがずれて error になり CI が落ちるので、該当テストの `# source:` を `hash` サブコマンドの値で更新する）
- sdd-init 通しE2E: `bash scripts/test-e2e-sdd-init.sh`（空プロジェクトで session-start → init-structure → update-claude-md を連鎖検証。en/ja テンプレート描画・custom root を含む。要 `python3` / `jq`。CI の `test` ジョブでも実行）
- Bend 証明ゲート: `bash scripts/proof-gate.sh`（要 `bend`。`.sdd/laws/**` の全法則ディレクトリに `run-verification.py proof` を実行し、PASS 以外は exit 1。CI では optional の `proof` ジョブ（ubuntu、`continue-on-error`、bend はバージョン固定 tarball から導入）が実行する。required ではない）
- プラグイン eval スイート: `/plugin-evals [--case '<feature>/*']`（実体は `bash .claude/skills/plugin-evals/scripts/run_evals.sh`。要 `claude` CLI 2.1.198 以降。認証は Claude Code のログインをそのまま使う。`plugins/sdd-workflow/evals/<feature>/<property>/` の各ケースは prose 実装 spec の決定表 1 行に対応し、`case.yaml` の `description` が spec の節を指す。regex グレーダーのみ。1 ケース約 10〜30 秒・$0.1〜0.3。1 回の全件実行で $4〜5 の課金が発生するため CI には**入れていない**（ローカル手動）。既知の不安定ケースはスキルの `references/known_unstable_cases.md` 参照）。散文でしか表せない性質は `.claude/skill-evals/` の assertion（`/evaluate-skills`、手動）が担う
- skill ヘルパースクリプト回帰: `bash scripts/test-skill-scripts.sh`（find-spec-docs.py / validate-files.py が custom root でキャッシュを設定 root 配下に生成するか検証。CI の `test` ジョブでも実行）
- プラグイン構造 Lint: CI の `plugin-lint` ジョブは2ステップで、`bash scripts/plugin-lint.sh`（構造・マニフェスト・front matter キー）と `python3 .claude/skills/plugin-lint/scripts/plugin_lint.py`（スキル `allowed-tools` のツール名妥当性・重複）を両方実行する。ローカルでも両方を流して exit 0 を確認する。2系統の役割分担と同期義務は `.claude/rules/scripts.md` を参照
- 公式バリデータ（ローカル手動）: `claude plugin validate ./plugins/sdd-workflow --strict` で Claude Code CLI 自身の検証を通す。認証不要でオフライン実行できるが、CI には**入れていない**（このリポジトリの CI は npm/node 依存を持たないため）。CI では `plugin-lint.sh` の Check 4.2（`agents/` にサブディレクトリを置かない・`agents/*.md` は front matter を持つ）が同等の不変条件を担保している
- Markdownリンクの整合性: 各ドキュメント内の相対リンクが有効か確認
- **IMPORTANT**: 新規エージェント追加時は `plugin.json` の `agents` 配列への登録を忘れずに（この配列はデフォルトの `agents/` スキャンを置き換えるため、未登録のエージェントはロードされない）。スキルは `skills/` が常にスキャンされるので登録不要（CONSTITUTION T-002 v2.0.0）
- プラグインデバッグ: `claude --debug` でプラグインの読み込み、フック実行、エージェント呼び出しの詳細ログを確認
- ローカルテスト: `claude --plugin-dir ./plugins/sdd-workflow` でローカルのプラグインを直接テスト
