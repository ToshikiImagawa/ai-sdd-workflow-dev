---
id: "design-task-implementation-checklist-generation"
title: "チェックリスト生成"
type: "design"
status: "draft"
sdd-phase: "plan"
impl-status: "implemented"
created: "2026-07-24"
updated: "2026-07-24"
depends-on: ["spec-task-implementation-checklist-generation"]
tags: ["checklist", "quality"]
category: "task-implementation"
priority: "medium"
risk: "medium"
---

# チェックリスト生成

**関連 Spec:** [checklist-generation_spec.md](checklist-generation_spec.md)
**関連 PRD:** [checklist-generation.md](../../requirement/task-implementation/checklist-generation.md)（親: [task-implementation](../../requirement/task-implementation/index.md)）
**準拠する原則:** [CONSTITUTION.md](../../CONSTITUTION.md) A-001（Skills-First）, B-001, B-002, D-001, D-002, T-002（plugin.json 登録）, T-003（文字化け防止）

---

# 1. 実装ステータス

**ステータス:** 🟢 実装済み

本設計書は既存実装（`skills/checklist/`）の挙動を逆算して記述したものである。
9 カテゴリ・`CHK-{category}{nn}` の ID 採番方式・優先度体系・入出力パス・テンプレート統合は
実装（Markdown プロンプト）を真実の源とする。

> **逆算記述の経緯（正当化）**: checklist スキルは AI-SDD ワークフローの初期構築時に実装が先行し、
> 本 spec/design はその後に機能仕様を明文化した逆算記述である。D-001（Specification-Driven）の原則に対し、
> 実装先行という経緯を [CONSTITUTION.md](../../CONSTITUTION.md) の例外プロセス（文書化・正当化・レビュー・追跡）
> に沿って本節に記録する。今後の変更は本 spec/design を真実の源として Specify → Plan → Tasks → Implement の
> フローに従う。

## 1.1. 実装進捗

| モジュール/機能           | ステータス | 備考                                                              |
|------------------------|--------|-------------------------------------------------------------------|
| checklist スキル         | 🟢     | `skills/checklist/SKILL.md`（`user-invocable: true`、`allowed-tools: Read/Write/Edit/Glob/Grep`） |
| 出力テンプレート          | 🟢     | `skills/checklist/templates/{en,ja}/checklist_template.md`           |
| フル出力例               | 🟢     | `skills/checklist/examples/checklist_full_example.md`（CHK-101〜CHK-903 の 9 カテゴリ 60 項目） |
| plugin.json 登録         | 🟢     | `skills` はディレクトリ参照 `./skills` で自動登録（T-002）                 |

---

# 2. 設計目標

- 仕様・設計・タスクから検証観点を**漏れなく抽出**し、9 カテゴリで整理する（FR-001 / FR-002）
- 項目 ID を**更新をまたいで安定**させ、完了状態の追跡を容易にする（NFR-001）
- 優先度（P1/P2/P3）で**マージ前の必須確認**を明確化する（FR-003）
- 出力言語を `SDD_LANG` に従い切り替える（FR-001 テンプレート / B-002 / NFR-002）
- 入出力パスを AI-SDD 命名規則・`SDD_*` 環境変数で解決する（NFR-003 / D-002）

---

# 3. 実装方式

| 領域     | 採用方式                                                        | 選定理由                                                                        |
|--------|-------------------------------------------------------------|-----------------------------------------------------------------------------|
| skill  | Markdown プロンプトスキル（`user-invocable: true`、Bash 不使用）        | 観点抽出・分類・優先度付けは Claude の判断を要する。A-001（Skills-First）に従いスキルとして実装。決定的コマンド実行が不要のため Bash を持たない |
| 抽出    | 各文書から観点を読み取り、カテゴリへマッピング                              | PRD=要求、spec=API/データモデル/振る舞い、design=構成/技術/判断、tasks=完了基準/依存という文書役割に応じて抽出する |
| ID 採番 | `CHK-{category}{nn}` 形式（カテゴリ番号 1〜9 + 連番）                  | カテゴリを ID プレフィックスに含めることで安定性と可読性を両立（NFR-001）                       |
| 多言語   | `SDD_LANG` 環境変数 + `templates/{en,ja}/checklist_template.md` | B-002 の一貫性要件。出力言語をテンプレートで切り替える                                     |
| パス解決 | `${CLAUDE_PROJECT_DIR}` + `SDD_*` 環境変数                       | 命名規則（requirement 無サフィックス／specification `_spec`/`_design`）を環境変数で解決（D-002） |

---

# 4. アーキテクチャ

## 4.1. システム構成図

```mermaid
graph TD
    U[開発者: /checklist feature ticket] --> SK[checklist SKILL.md]
    SK -->|読み込み| PRD[PRD *.md]
    SK -->|読み込み 必須| SPEC[*_spec.md]
    SK -->|読み込み 必須| DES[*_design.md]
    SK -->|読み込み 任意| TASKS[tasks.md]
    SK -->|観点抽出→9 カテゴリ分類| GEN[CHK-ID 採番・優先度付け]
    GEN -->|SDD_LANG| TPL[templates/en or ja]
    GEN -->|保存| OUT[task/{ticket}/checklist.md]
```

## 4.2. モジュール分割

| モジュール名                | 責務                                                             | 依存関係         | 配置場所                                              |
|--------------------------|----------------------------------------------------------------|----------------|---------------------------------------------------|
| checklist SKILL.md       | 文書読み込み・観点抽出・カテゴリ分類・ID 採番・優先度付け・保存・報告          | SDD_LANG, SDD_* | `plugins/sdd-workflow/skills/checklist/SKILL.md`    |
| checklist_template       | チェックリスト出力の基底フォーマット（日英）                             | SDD_LANG        | `plugins/sdd-workflow/skills/checklist/templates/{en,ja}/` |
| checklist_full_example   | 全 9 カテゴリ・優先度・完了基準を含むフル出力例                          | -              | `plugins/sdd-workflow/skills/checklist/examples/`   |

---

# 5. データ構造

## 5.1. 9 カテゴリと ID プレフィックス

| カテゴリ番号 | カテゴリ名（実装原語）          | ID 例      | 抽出元の主眼                         |
|:----------|:---------------------------|:----------|:-----------------------------------|
| 1         | Requirements Review        | CHK-1xx   | PRD の FR-xxx / NFR-xxx カバレッジ    |
| 2         | Specification Review       | CHK-2xx   | 公開 API・データモデル                 |
| 3         | Design Review              | CHK-3xx   | アーキテクチャ・技術スタック・設計判断     |
| 4         | Implementation Review      | CHK-4xx   | コード構造・命名規約                    |
| 5         | Testing Review             | CHK-5xx   | 単体・統合テスト・エッジケース            |
| 6         | Documentation Review       | CHK-6xx   | コメント・設計書・README               |
| 7         | Security Review            | CHK-7xx   | 認証・認可・入力検証                     |
| 8         | Performance Review         | CHK-8xx   | 応答時間・リソース使用                   |
| 9         | Deployment Review          | CHK-9xx   | 設定・マイグレーション・ロールバック計画     |

## 5.2. 優先度体系

| 優先度 | マーク | 基準                 | 確認タイミング       |
|:-----|:-----|:--------------------|:----------------|
| P1   | P1   | マージ前に必ず通過        | PR 作成前         |
| P2   | P2   | マージ前に通過すべき       | PR レビュー中       |
| P3   | P3   | あると望ましい           | 機会があれば         |

## 5.3. チェックリスト項目構造（概念）

```markdown
### CHK-{category}{nn}: {項目タイトル} [P1|P2|P3]

- 検証内容: {何を確認するか}
- 完了基準: {満たされたと判定できる条件}
- 抽出元: {FR-xxx / spec セクション / design セクション / task}
```

---

# 6. ファイル構成

```
plugins/sdd-workflow/
├── skills/checklist/
│   ├── SKILL.md                              # ユーザー呼び出しスキル本体
│   ├── examples/checklist_full_example.md    # 9 カテゴリ 60 項目のフル出力例
│   └── templates/{en,ja}/checklist_template.md  # 出力基底テンプレート（日英）
└── .claude-plugin/plugin.json                # skills は "./skills" 参照で自動登録（T-002）
```

checklist スキルは実装・登録済みであり、本設計書は逆算文書である。
新規追加ではないため plugin.json の変更は発生しない（既存登録の維持を確認する）。

---

# 7. 非機能要件実現方針

| 要件                    | 実現方針                                                                     |
|-----------------------|------------------------------------------------------------------------------|
| NFR-001（ID 安定性）      | `CHK-{category}{nn}` 形式でカテゴリを ID に固定。`--update` 時も既存 ID と完了状態を保持 |
| NFR-002（多言語・一貫性）   | `SDD_LANG` に応じ `templates/{en,ja}/` を切り替え。日英で同等構成を維持（B-002）      |
| NFR-003（命名規則）       | 入出力パスを `SDD_*` 環境変数で解決し、requirement 無サフィックス／spec・design サフィックスを厳守（D-002） |

---

# 8. テスト戦略

| テストレベル | 対象                            | カバレッジ目標                                   |
|:----------|:------------------------------|:----------------------------------------------|
| 構文検証    | `skills/checklist/`            | plugin-lint（プロンプト Markdown 構文・命名規則）が通ること |
| 手動検証    | デモンストレーション                | 観点抽出・9 カテゴリ分類・ID 採番・優先度付けが機能すること（FR-001〜004） |
| 整合性確認  | 生成後の `checklist.md`          | run-checklist が CHK-ID・優先度を解釈できること           |

---

# 9. 設計判断

## 9.1. 決定事項

| 決定事項            | 選択肢                          | 決定内容                          | 理由                                                            |
|-------------------|-------------------------------|--------------------------------|---------------------------------------------------------------|
| 実装層             | スキル単体 / スキル + エージェント    | スキル単体                        | 観点抽出・分類は単一スキルで完結し、分析専用エージェントを分離する必要がない       |
| ツール権限          | Bash 含む / 読み書き系のみ         | Read/Write/Edit/Glob/Grep（Bash 不使用） | チェックリスト生成は決定的コマンド実行を要さない。生成は Write/Edit で行う         |
| ID 体系            | 連番のみ / カテゴリ + 連番          | `CHK-{category}{nn}`             | カテゴリをプレフィックスに含め、更新時の安定性と分類の可読性を両立（NFR-001）        |
| 抽出元の必須性       | 全文書必須 / spec・design 必須       | spec・design を必須、PRD・tasks は任意 | 仕様・設計は検証観点の中核。PRD・tasks は補助情報として存在時に活用            |
| 保存先             | 任意パス / task ディレクトリ配下     | `${SDD_TASK_PATH}/{ticket}/checklist.md` | run-checklist の入力位置と一致させ、ワークフロー連携を成立させる（親 PRD IR_001） |

## 9.2. 未解決の課題

| 課題                                | 影響度 | 対応方針                                                  |
|-----------------------------------|-----|-----------------------------------------------------------|
| 抽出品質の基盤モデル依存              | 中   | 抽出観点表・カテゴリ定義を精緻化。意味論的抽出の限界はスコープ外          |
| `--export` 連携先（GitHub/CSV）の仕様固定 | 低   | 現状は出力例に依存。将来のフォーマット明文化を検討                    |

---

# 10. 原則準拠チェックリスト

| 原則ID  | 原則名                    | 準拠状況 | 備考                                                       |
|-------|--------------------------|--------|------------------------------------------------------------|
| A-001 | Skills-First              | ✅     | `skills/checklist/` として実装（legacy commands 不使用）        |
| B-001 | Vibe Coding 防止          | ✅     | 検証観点を仕様・設計から機械的に導出し、発明を排除                    |
| B-002 | 多言語対応（EN/JA）の一貫性 | ✅     | `templates/{en,ja}/` と `SDD_LANG` による出力言語切り替え          |
| D-001 | Specification-Driven      | ✅     | 仕様書・設計書を真実の源として観点を抽出                            |
| D-002 | ファイル命名規則の厳守      | ✅     | 入出力パスで requirement 無サフィックス／spec・design サフィックスを厳守  |
| T-002 | plugin.json 登録の徹底     | ✅     | `./skills` 参照で自動登録済み                                   |
| T-003 | 日本語出力の文字化け防止     | ✅     | 日本語テンプレート・本設計書に U+FFFD / mojibake を含めない            |

**原則から逸脱する場合**: 理由を「9.1. 決定事項」に明記し、CONSTITUTION.md の例外プロセスに従うこと。
