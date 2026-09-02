# リポジトリ構成

```
ai-sdd-workflow/
├── .claude-plugin/
│   └── marketplace.json           # マーケットプレイスメタデータ
├── .agents/skills/                # Codex向け開発スキル
├── .claude/
│   ├── rules/                     # トピック別開発ルール（7ファイル。CLAUDE.md から参照）
│   ├── skills/                    # Claude Code向け開発スキル
│   └── tests/                     # SDD有効/無効のA/B計測ハーネス
│       ├── RUNBOOK.md             # 計測手順
│       └── harness/               # run_ab.sh / verify_parity.sh / 集計Python / prompts/
├── .github/workflows/             # CI（ci.yml / prepare-release.yml / release.yml）
├── plugins/
│   └── sdd-workflow/              # 統合プラグイン（多言語対応）
│       ├── .claude-plugin/
│       │   └── plugin.json        # プラグインマニフェスト（agents 6件のみ登録）
│       ├── agents/
│       │   ├── spec-reviewer.md   # 仕様書レビューエージェント
│       │   ├── prd-reviewer.md    # PRDレビューエージェント
│       │   ├── requirement-analyzer.md  # 要求仕様分析エージェント
│       │   ├── clarification-assistant.md  # 仕様明確化アシスタント
│       │   ├── front-matter-reviewer.md  # front matter検証エージェント
│       │   └── cross-prd-reviewer.md  # PRD横断整合レビューエージェント
│       ├── skills/                # 19スキル
│       │   ├── analyze-requirements/       # 要求分析（UR/FR/NFR抽出）
│       │   ├── check-spec/                 # 実装とspecの整合性チェック
│       │   │   ├── scripts/
│       │   │   └── templates/{en,ja}/
│       │   ├── checklist/                  # 品質チェックリスト生成
│       │   │   └── templates/{en,ja}/
│       │   ├── clarify/                    # 仕様明確化
│       │   │   └── templates/{en,ja}/
│       │   ├── constitution/               # プロジェクト原則管理
│       │   │   ├── scripts/
│       │   │   └── templates/{en,ja}/
│       │   ├── doc-consistency-checker/    # ドキュメント整合性チェッカー
│       │   │   └── templates/{en,ja}/
│       │   ├── finalize-prd/               # PRD統合・完成
│       │   │   └── templates/{en,ja}/
│       │   ├── generate-prd/               # PRD生成
│       │   │   ├── scripts/
│       │   │   └── templates/{en,ja}/
│       │   ├── generate-requirements-diagram/  # SysML要求図生成
│       │   ├── generate-spec/              # 仕様書・設計書生成
│       │   │   ├── scripts/
│       │   │   └── templates/{en,ja}/
│       │   ├── generate-usecase-diagram/   # ユースケース図生成
│       │   ├── implement/                  # TDD実装
│       │   │   └── templates/{en,ja}/
│       │   ├── plan-refactor/              # リファクタリング計画
│       │   │   ├── scripts/
│       │   │   └── templates/{en,ja}/
│       │   ├── recommend-front-matter/     # front matter推奨
│       │   │   ├── scripts/
│       │   │   └── templates/{en,ja}/
│       │   ├── run-checklist/              # チェックリスト自動検証
│       │   │   └── templates/{en,ja}/
│       │   ├── sdd-init/                   # AI-SDDワークフロー初期化
│       │   │   ├── scripts/
│       │   │   └── templates/{en,ja}/
│       │   ├── task-breakdown/             # タスク分解
│       │   │   └── templates/{en,ja}/
│       │   ├── task-cleanup/               # タスククリーンアップ
│       │   │   └── templates/{en,ja}/
│       │   └── vibe-detector/              # Vibe Coding検出
│       │       └── templates/{en,ja}/
│       ├── shared/                # スキル・エージェント共通のサポートファイル
│       │   ├── references/        # 共通の参照資料（20ファイル）
│       │   ├── examples/          # エージェント利用例（7ファイル）
│       │   └── templates/{en,ja}/ # エージェント出力テンプレート（各8ファイル）
│       ├── hooks/
│       │   └── hooks.json         # フック設定（JSON形式）
│       ├── scripts/
│       │   ├── session-start.py   # セッション開始時の初期化
│       │   ├── user-prompt-submit.py  # Vibe Coding兆候検知
│       │   ├── pre-tool-use.py    # .sdd/ ファイル命名規則検証・CONSTITUTION原則注入
│       │   ├── post-tool-use.py   # ドキュメント更新漏れ検知
│       │   ├── sdd_index.py       # .sdd/ ドキュメントの構造化インデックス生成
│       │   ├── hook_common.py     # 共通ヘルパー（stdin/stdout・パス解決・.sdd-config読込）
│       │   ├── fm_parser.py       # 共有: front matter 検出・パース
│       │   ├── naming.py          # 共有: 命名規則検証・ドキュメント種別判定
│       │   ├── doc_walker.py      # 共有: 対象ドキュメント走査・design doc探索
│       │   └── env_export.py      # 共有: CLAUDE_ENV_FILE への export 書き出し
│       ├── AI-SDD-PRINCIPLES.source.md
│       ├── LICENSE
│       ├── README.md
│       ├── README.ja.md
│       ├── CHANGELOG.md
│       └── CHANGELOG.ja.md
├── scripts/                        # 検証・Lint・テスト用シェルスクリプト（`.sh` 6本）
├── tests/                          # Python ユニットテスト（pytest。fixtures/ を含む）
├── dist/
│   └── README.md                   # 配布リポジトリ用README
├── CLAUDE.md                       # 共通プロジェクト指示（正本）
├── PLUGIN_AGENTS.md                # プラグインエージェント設計ガイド
├── PLUGIN.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── README.md
```

## 補足

- **スキルのサポートディレクトリ**: 上のツリーは `templates/` と `scripts/` のみを示している。多くのスキルは
  `references/`（全19スキル）と `examples/`（9スキル）も持つ。`templates/` を持つのは16スキル、
  `scripts/` を持つのは7スキル（check-spec / constitution / generate-prd / generate-spec / plan-refactor /
  recommend-front-matter / sdd-init）
- **`plugin.json` の登録範囲**: `agents` 配列（6件）のみを宣言する。`skills` / `hooks` は宣言しない
  （CONSTITUTION T-002 v2.0.0）。`agents` はデフォルトの `agents/` スキャンを**置き換える**ため宣言が必須だが、
  `skills` は常にスキャンされるので宣言が冗長、`hooks` は標準パスを宣言すると二重ロードになる。
  新規エージェント追加時のみ `plugin.json` の更新が必要
- **`shared/references/`**: 複数のスキル・エージェントから参照される共通資料（20ファイル）。エージェントの参照資料も
  ここに集約している。`plugin-lint` の Check 2 でスキル配下のサポートファイルと同じ命名規則・拡張子規則が適用される
- **`agents/` にはエージェント定義のみを置く**: `templates/` / `references/` / `examples/` などのサポートファイルは
  `shared/` 配下に置き、エージェント本文からは `${CLAUDE_PLUGIN_ROOT}/shared/...` 形式で参照する。
  `claude plugin validate --strict` は `agents/**` を再帰走査するため、`agents/` 配下のサポートファイルは
  エージェント定義として扱われ検証エラーになる（`plugin-lint.sh` の Check 4.2 が同じ不変条件を検査する）
- **ルート直下の `scripts/` と `tests/`**: 検証コマンドの詳細は
  [scripts.md](scripts.md) / [testing-and-verification.md](testing-and-verification.md) を参照
