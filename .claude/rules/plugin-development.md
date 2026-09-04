---
paths:
  - "plugins/**"
---

# プラグイン開発

## 開発時の注意

- プラグイン修正時は `plugins/sdd-workflow/` に限定して作業
- 「調査して」と依頼された場合は、まずスコープを確認してから探索

### `.sdd/` の生成物は「インストール済みプラグイン」に追従する

次の2ファイルは SessionStart フックが `${CLAUDE_PLUGIN_ROOT}`（= **インストール済み**プラグイン）から
自動生成する。**開発中の `plugins/sdd-workflow/` から手で同期してはならない。**

| ファイル | 生成元 |
|:---|:---|
| `.sdd/AI-SDD-PRINCIPLES.md` | `${CLAUDE_PLUGIN_ROOT}/AI-SDD-PRINCIPLES.source.md` |
| `.claude/rules/ai-sdd-instructions.md` | `${CLAUDE_PLUGIN_ROOT}/skills/sdd-init/templates/ai_sdd_instructions_rules.md` |

**理由**: このリポジトリはリリース済みのプラグインで自分自身を dogfooding している。セッション中に実際に
動いているスキル・フックはインストール版であり、開発中の未リリース版ではない。`.sdd/` に未リリース版の
原則を置くと、AIは**動いているスキルが実装していない規則**に従うことになり、`.sdd/` 配下の実ドキュメント
（v4系の永続 `*_design.md` など）とも食い違う。

**更新タイミング**: これらが更新されるのは、**リリース後にインストール済みプラグインのバージョンを上げた時**
だけ。開発中のPRで内容が変わって見えるのは、開発ソースを先取りして同期してしまった兆候なので、
`git restore` でフックの出力に戻す。

`plugins/sdd-workflow/AI-SDD-PRINCIPLES.source.md` は「**これから作るもの**」の正典、
`.sdd/AI-SDD-PRINCIPLES.md` は「**いま従うもの**」の正典であり、両者がリリースまで一致しないのは正常。

## プラグインエージェント設計ガイド

AI-SDDワークフロープラグインのサブエージェント設計・実装に関する原則とベストプラクティスは、
[PLUGIN_AGENTS.md](../../PLUGIN_AGENTS.md) を参照してください。

このガイドでは以下の内容を定義しています：

1. **サブエージェントの基本概念**（コンテキスト独立性、トークン効率化）
2. **エージェント設計原則**（役割、入出力、allowed-tools/tools/skills/hooks、前提条件）
3. **委任すべきタスク vs メインで実行すべきタスク**
4. **エージェント間連携パターン**（スキル連携、フック連携を含む）
5. **実践Tips**（デバッグ方法、`claude --debug` の活用）

## プラグイン開発ガイド

Claude Codeプラグインとマーケットプレイスの作成に関する包括的なガイドは、[PLUGIN.md](../../PLUGIN.md) を参照してください。

このガイドでは以下の内容を定義しています：

1. **プラグイン基本構造**（ディレクトリレイアウト、マーケットプレイス構成）
2. **マニフェストファイル**（plugin.json のコンポーネントパスフィールド、`${CLAUDE_PLUGIN_ROOT}` 環境変数）
3. **コマンド（legacy）、エージェント、スキルの実装**（フロントマター、`context: fork`、動的コンテキスト注入）
4. **MCP / LSP サーバー連携**（外部ツール統合、Language Server Protocol 統合）
5. **フック実装**（JSON形式の `hooks.json`、イベント一覧、フックタイプ: command/prompt/agent）
6. **プラグインキャッシュとインストールスコープ**（user/project/local/managed）
7. **マーケットプレイス公開プロセス**（品質基準、配布モデル）
8. **CLI コマンドリファレンス / デバッグ**

## モデル表記方針

エージェント・スキルでモデルを指定する際は、**エイリアス表記（`sonnet` / `haiku` 等）を維持**し、具体バージョン（`claude-haiku-4-5-*` 等）には固定しない。

- **理由**: 配布プラグインとして常に最新世代を追従でき、表記が簡潔。世代更新のたびの手動更新が不要。
- **キー**: スキル・エージェントとも `model:` でモデルを選ぶ。スキルの `agent:` は
  **モデルではなくサブエージェント型名**（`Explore` / `general-purpose` 等）の指定であり、`context: fork`
  を設定したときにのみ効く。ここにモデル名を書いても警告なく `general-purpose` にフォールバックし、
  モデル指定は無効になる。
- **トレードオフ**: 世代更新で挙動が変わりうるため、品質退行は CI テストで検知する。

## 新しいプラグインの追加

1. `plugins/{plugin-name}/` ディレクトリを作成
2. `.claude-plugin/plugin.json` にプラグインマニフェストを配置
3. agents, skills, hooks を必要に応じて追加（新規コマンドは `skills/` を推奨）
4. `.claude-plugin/marketplace.json` の `plugins` 配列に追加
