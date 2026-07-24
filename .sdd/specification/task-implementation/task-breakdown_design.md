---
id: "design-task-implementation-task-breakdown"
title: "タスク分解"
type: "design"
status: "draft"
sdd-phase: "plan"
impl-status: "implemented"
created: "2026-07-24"
updated: "2026-07-24"
depends-on: ["spec-task-implementation-task-breakdown"]
tags: ["task-breakdown", "tasks"]
category: "task-implementation"
priority: "high"
risk: "high"
---

# タスク分解

**関連 Spec:** [task-breakdown_spec.md](task-breakdown_spec.md)
**関連 PRD:** [task-breakdown.md](../../requirement/task-implementation/task-breakdown.md)（親: [task-implementation](../../requirement/task-implementation/index.md)）
**準拠する原則:** [CONSTITUTION.md](../../CONSTITUTION.md) A-001（Skills-First）, B-001, B-002, D-001, D-002, T-002（plugin.json 登録）, T-003（文字化け防止）

---

# 1. 実装ステータス

**ステータス:** 🟢 実装済み

本設計書は既存実装（`skills/task-breakdown/`）の挙動を逆算して記述したものである。
処理フロー（文書読み込み → 設計書分析 → 分解原則 → 分類 → 依存整理 → 出力）・タスクカテゴリ・
front matter 生成規則・Serena MCP 連携・入出力パス・テンプレートは実装（Markdown プロンプトおよび
`references/` / `examples/` / `templates/{en,ja}/`）を真実の源とする。

> **逆算記述の経緯（正当化）**: task-breakdown スキルは AI-SDD ワークフローの初期構築時に実装が先行し、
> 本 spec/design はその後に機能仕様を明文化した逆算記述である。D-001（Specification-Driven）の原則に対し、
> 実装先行という経緯を [CONSTITUTION.md](../../CONSTITUTION.md) の例外プロセス（文書化・正当化・レビュー・追跡）
> に沿って本節に記録する。今後の変更は本 spec/design を真実の源として Specify → Plan → Tasks → Implement の
> フローに従う。

## 1.1. 実装進捗

| モジュール/機能          | ステータス | 備考                                                                |
|-----------------------|--------|---------------------------------------------------------------------|
| task-breakdown スキル    | 🟢     | `skills/task-breakdown/SKILL.md`（`user-invocable: true`、`allowed-tools: Read/Write/Edit/Glob/Grep/AskUserQuestion`） |
| 依存関係図参照           | 🟢     | `skills/task-breakdown/references/task_dependency_diagram.md`         |
| 出力例・カバレッジ例       | 🟢     | `skills/task-breakdown/examples/`（task_list_format / requirement_coverage / serena_analysis） |
| 出力テンプレート         | 🟢     | `skills/task-breakdown/templates/{en,ja}/breakdown_output.md`         |
| plugin.json 登録         | 🟢     | `skills` はディレクトリ参照 `./skills` で自動登録（T-002）                  |

---

# 2. 設計目標

- 技術設計書を分析し、**独立テスト可能**な粒度へタスクを分解する（FR-001 / FR-002 / NFR-001）
- タスクを **5 カテゴリ**へ分類し依存関係を整理する（FR-003）
- tasks.md を **task ディレクトリ配下**へ front matter 付きで保存する（FR-004 / NFR-003）
- PRD/spec がある場合は **要求カバレッジ**を検証する（FR-005）
- 出力言語を `SDD_LANG` に従い切り替える（B-002 / NFR-002）

---

# 3. 実装方式

| 領域     | 採用方式                                                              | 選定理由                                                                          |
|--------|-------------------------------------------------------------------|-----------------------------------------------------------------------------|
| skill  | Markdown プロンプトスキル（`user-invocable: true`、Bash 不使用）           | 設計書分析・タスク分解は Claude の判断を要する。A-001 に従いスキルとして実装。決定的コマンドが不要のため Bash を持たない |
| ツール   | `Read/Write/Edit/Glob/Grep/AskUserQuestion`                        | 文書読み込みと生成・保存に読み書き系、設計書欠如時の確認に AskUserQuestion が必要             |
| 分解原則 | 独立性・テスト可能性・適切な粒度を references/templates で定義              | 独立テスト可能性（NFR_001）を分解基準として明示する                                       |
| 依存整理 | Mermaid 依存関係図（`references/task_dependency_diagram.md`）          | タスク間依存を可視化し、実装順序の錯綜を防ぐ                                             |
| MCP 連携 | Serena MCP を任意連携（`.mcp.json` 設定時）                             | 影響範囲分析・依存自動検出で精度向上。未設定でも設計書ベースで分解可能に保つ                    |
| 多言語   | `SDD_LANG` 環境変数 + `templates/{en,ja}/breakdown_output.md`         | B-002 の一貫性要件。出力形式をテンプレートで切り替える                                    |

---

# 4. アーキテクチャ

## 4.1. システム構成図

```mermaid
graph TD
    U[開発者: /task-breakdown feature ticket] --> SK[task-breakdown SKILL.md]
    SK -->|必須| DES[*_design.md]
    SK -->|任意| PRD[PRD *.md]
    SK -->|任意| SPEC[*_spec.md]
    SK -->|分析| EX[モジュール/依存/IF/技術スタック抽出]
    EX -->|分解原則| BD[独立テスト可能な小タスク]
    BD -->|5 カテゴリ分類| CAT[Foundation/Core/Integration/Testing/Finishing]
    CAT -->|依存整理| DEP[依存関係図]
    SK -.->|任意| SERENA[Serena MCP 影響範囲分析]
    DEP -->|カバレッジ検証| COV[要求カバレッジ表]
    COV -->|SDD_LANG| TPL[templates/en or ja]
    TPL -->|保存| OUT[task/{ticket}/tasks.md]
```

## 4.2. モジュール分割

| モジュール名                | 責務                                                          | 依存関係            | 配置場所                                                  |
|--------------------------|-------------------------------------------------------------|-------------------|-------------------------------------------------------|
| task-breakdown SKILL.md  | 文書読み込み・設計書分析・分解・分類・依存整理・カバレッジ検証・保存・報告   | SDD_LANG, SDD_*, (Serena MCP 任意) | `plugins/sdd-workflow/skills/task-breakdown/SKILL.md`   |
| task_dependency_diagram  | タスク間依存の Mermaid 図の例                                    | -                 | `plugins/sdd-workflow/skills/task-breakdown/references/` |
| breakdown_output         | タスク一覧出力の基底テンプレート（日英）                             | SDD_LANG          | `plugins/sdd-workflow/skills/task-breakdown/templates/{en,ja}/` |
| examples/                | タスク一覧形式・要求カバレッジ・Serena 分析の例                      | -                 | `plugins/sdd-workflow/skills/task-breakdown/examples/`  |

---

# 5. データ構造

## 5.1. タスクカテゴリ（実装準拠）

| カテゴリ（実装原語）  | 説明                        | 例                              |
|:------------------|:--------------------------|:-------------------------------|
| Foundation        | 他タスクの前提となる作業        | ディレクトリ構造・型定義            |
| Core              | 主要機能の実装                | ビジネスロジック・API              |
| Integration       | モジュール間の連携             | サービス層・イベント処理            |
| Testing           | テスト作成                   | 単体テスト・統合テスト              |
| Finishing         | 最終調整                     | ドキュメント更新・リファクタリング      |

## 5.2. tasks.md front matter（概念）

```yaml
id: "task-{feature-name}"        # 階層時: "task-{parent}-{feature-name}"
type: "task"
status: "pending"                # 新規分解時
sdd-phase: "tasks"
depends-on: ["design-{feature-name}"]
ticket: "{ticket-number}"        # 入力引数がある場合
tags: []                         # 設計書から継承
category: ""                     # 設計書から継承
priority: ""                     # 設計書から継承
```

---

# 6. ファイル構成

```
plugins/sdd-workflow/
├── skills/task-breakdown/
│   ├── SKILL.md                              # ユーザー呼び出しスキル本体
│   ├── references/task_dependency_diagram.md # 依存関係図の例
│   ├── examples/                             # task_list_format / requirement_coverage / serena_analysis
│   └── templates/{en,ja}/breakdown_output.md # 出力基底テンプレート（日英）
└── .claude-plugin/plugin.json                # skills は "./skills" 参照で自動登録（T-002）
```

task-breakdown スキルは実装・登録済みであり、本設計書は逆算文書である。
新規追加ではないため plugin.json の変更は発生しない（既存登録の維持を確認する）。

---

# 7. 非機能要件実現方針

| 要件                     | 実現方針                                                                       |
|------------------------|------------------------------------------------------------------------------|
| NFR-001（粒度）          | 独立性・テスト可能性・適切な粒度を分解原則として適用し、各タスクに完了基準を対応づける          |
| NFR-002（多言語・一貫性）  | `SDD_LANG` に応じ `templates/{en,ja}/` を切り替え。日英で同等構成を維持（B-002）        |
| NFR-003（命名規則）      | 入出力パス・task front matter スキーマを厳守（requirement 無サフィックス／spec・design サフィックス・D-002） |

---

# 8. テスト戦略

| テストレベル | 対象                              | カバレッジ目標                                        |
|:----------|:--------------------------------|:----------------------------------------------------|
| 構文検証    | `skills/task-breakdown/`         | plugin-lint（プロンプト Markdown 構文・命名規則）が通ること        |
| 手動検証    | デモンストレーション                  | 設計書分析・分解・分類・依存整理・カバレッジ検証が機能すること（FR-001〜005） |
| 整合性確認  | 生成後の `tasks.md`                | front matter スキーマ・要求カバレッジ表が妥当であること              |

---

# 9. 設計判断

## 9.1. 決定事項

| 決定事項            | 選択肢                        | 決定内容                              | 理由                                                          |
|-------------------|-----------------------------|-------------------------------------|---------------------------------------------------------------|
| 実装層             | スキル単体 / スキル + エージェント    | スキル単体                            | 設計書分析・分解は単一スキルで完結する                              |
| Bash 権限          | 含む / 含まない                 | 含まない（Read/Write/Edit/Glob/Grep/AskUserQuestion） | 分解は決定的コマンド実行を要さない。生成は Write/Edit で行う             |
| 設計書欠如時の挙動    | 常にエラー / モード分岐          | `--ci` はエラー終了、対話は generate-spec を促す | CI では確定的に失敗させ、対話では次アクションを案内する（FR-002）           |
| 依存の表現          | テキストのみ / Mermaid 図        | Mermaid 依存関係図                     | 依存を可視化し実装順序の錯綜を防ぐ                                    |
| Serena MCP         | 必須 / 任意連携                 | 任意連携（未設定でも動作）              | 精度向上は歓迎するが、外部 MCP 依存を必須にしない                        |
| カバレッジ検証        | 常時 / PRD-spec 存在時          | PRD/spec 存在時に検証                  | 上流要求がある場合のみ FR/NFR/API のカバレッジを担保（FR-005）            |

## 9.2. 未解決の課題

| 課題                                   | 影響度 | 対応方針                                          |
|--------------------------------------|-----|---------------------------------------------------|
| 分解粒度の基盤モデル依存                 | 中   | 分解原則・粒度基準テンプレートを精緻化。過大タスクは再分解を促す      |
| Serena 未対応言語での影響範囲分析の限界    | 低   | 未対応時は手動確認を推奨する旨を明記                        |

---

# 10. 原則準拠チェックリスト

| 原則ID  | 原則名                    | 準拠状況 | 備考                                                       |
|-------|--------------------------|--------|------------------------------------------------------------|
| A-001 | Skills-First              | ✅     | `skills/task-breakdown/` として実装（legacy commands 不使用）    |
| B-001 | Vibe Coding 防止          | ✅     | 設計書を入力の前提とし、要求カバレッジで推測タスクを排除              |
| B-002 | 多言語対応（EN/JA）の一貫性 | ✅     | `templates/{en,ja}/` と `SDD_LANG` による出力言語切り替え          |
| D-001 | Specification-Driven      | ✅     | 技術設計書を真実の源として分解                                    |
| D-002 | ファイル命名規則の厳守      | ✅     | 入出力パス・task front matter スキーマを厳守                       |
| T-002 | plugin.json 登録の徹底     | ✅     | `./skills` 参照で自動登録済み                                   |
| T-003 | 日本語出力の文字化け防止     | ✅     | 日本語テンプレート・本設計書に U+FFFD / mojibake を含めない            |

**原則から逸脱する場合**: 理由を「9.1. 決定事項」に明記し、CONSTITUTION.md の例外プロセスに従うこと。
