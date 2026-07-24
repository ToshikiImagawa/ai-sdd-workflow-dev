---
id: "design-task-implementation-task-cleanup"
title: "タスククリーンアップ"
type: "design"
status: "draft"
sdd-phase: "plan"
impl-status: "implemented"
created: "2026-07-24"
updated: "2026-07-24"
depends-on: ["spec-task-implementation-task-cleanup"]
tags: ["task-cleanup", "knowledge-persistence"]
category: "task-implementation"
priority: "medium"
risk: "medium"
---

# タスククリーンアップ

**関連 Spec:** [task-cleanup_spec.md](task-cleanup_spec.md)
**関連 PRD:** [task-cleanup.md](../../requirement/task-implementation/task-cleanup.md)（親: [task-implementation](../../requirement/task-implementation/index.md)）
**準拠する原則:** [CONSTITUTION.md](../../CONSTITUTION.md) A-001（Skills-First）, B-002, D-001, D-003（永続性ルール）, T-002（plugin.json 登録）, T-003（文字化け防止）

---

# 1. 実装ステータス

**ステータス:** 🟢 実装済み

本設計書は既存実装（`skills/task-cleanup/`）の挙動を逆算して記述したものである。
処理フロー（対象特定 → ファイル確認 → 分類 → 統合先決定 → 統合 → front matter 更新 → 削除）・
統合／削除の分類基準・削除方式（`git rm`）・実行モデル（`agent: haiku`）・入出力パス・テンプレートは
実装（Markdown プロンプトおよび `examples/` / `templates/{en,ja}/`）を真実の源とする。

> **逆算記述の経緯（正当化）**: task-cleanup スキルは AI-SDD ワークフローの初期構築時に実装が先行し、
> 本 spec/design はその後に機能仕様を明文化した逆算記述である。D-001（Specification-Driven）の原則に対し、
> 実装先行という経緯を [CONSTITUTION.md](../../CONSTITUTION.md) の例外プロセス（文書化・正当化・レビュー・追跡）
> に沿って本節に記録する。今後の変更は本 spec/design を真実の源として Specify → Plan → Tasks → Implement の
> フローに従う。

## 1.1. 実装進捗

| モジュール/機能          | ステータス | 備考                                                                |
|-----------------------|--------|---------------------------------------------------------------------|
| task-cleanup スキル      | 🟢     | `skills/task-cleanup/SKILL.md`（`user-invocable: true`、`agent: haiku`、`allowed-tools: Read/Write/Edit/Glob/Grep/Bash/AskUserQuestion`） |
| 範囲確認例              | 🟢     | `skills/task-cleanup/examples/scope_confirmation.md`                  |
| 出力テンプレート         | 🟢     | `skills/task-cleanup/templates/{en,ja}/cleanup_output.md`             |
| plugin.json 登録         | 🟢     | `skills` はディレクトリ参照 `./skills` で自動登録（T-002）                  |

---

# 2. 設計目標

- 価値ある設計知見を**確実に統合**し、削除可能な作業ログと**選別**する（FR-001 / FR-002）
- **統合完了後にのみ削除**し、統合前削除を発生させない（FR-003 / NFR-001 / DC_002 / D-003）
- 統合に伴い関連文書の **front matter を更新**する（FR-004）
- 引数なし実行時は**範囲確認**でユーザー承認を得る（FR-005 / NFR-001）
- 出力言語を `SDD_LANG` に従い切り替える（B-002 / NFR-002）

---

# 3. 実装方式

| 領域     | 採用方式                                                              | 選定理由                                                                          |
|--------|-------------------------------------------------------------------|-----------------------------------------------------------------------------|
| skill  | Markdown プロンプトスキル（`user-invocable: true`、`agent: haiku`）        | 知見の選別・統合は判断を要するが定型度が高い。軽量モデル（haiku）でコスト効率よく実行。A-001 に従いスキルとして実装 |
| ツール   | `Read/Write/Edit/Glob/Grep/Bash/AskUserQuestion`                   | ファイル一覧・更新日確認・削除に Bash（`ls`/`git log`/`git rm`）、統合に Edit/Write、範囲確認に AskUserQuestion が必要 |
| 削除    | `git rm`（ファイル単位）/ `git rm -r`（ディレクトリ）                     | 削除を Git 管理下で行い履歴の追跡と取り消しを可能にする                                    |
| 順序保証 | 統合 → front matter 更新 → 削除の順を処理フローで固定                     | 統合前削除の禁止（DC_002 / D-003）をプロセス順序として担保                                |
| 多言語   | `SDD_LANG` 環境変数 + `templates/{en,ja}/cleanup_output.md`           | B-002 の一貫性要件。出力形式をテンプレートで切り替える                                    |

---

# 4. アーキテクチャ

## 4.1. システム構成図

```mermaid
graph TD
    U[開発者: /task-cleanup ticket] --> SK[task-cleanup SKILL.md]
    SK -->|引数なし| CONF[範囲確認 AskUserQuestion]
    SK -->|1 対象特定| TGT[task/{ticket}/ or task/ 全体]
    TGT -->|2 ファイル確認 ls/git log| LIST[ファイル一覧・最終更新日]
    LIST -->|3 分類| CLS{統合対象 / 削除可能}
    CLS -->|統合対象| MERGE[最も関連する *_design.md へ統合]
    MERGE -->|4 front matter 更新| FM[impl-status/updated/status]
    FM -->|5 統合完了後| DEL[git rm でファイル/ディレクトリ削除]
    CLS -->|削除可能| DEL
    SK -->|SDD_LANG| TPL[templates/en or ja]
```

## 4.2. モジュール分割

| モジュール名                | 責務                                                          | 依存関係            | 配置場所                                                |
|--------------------------|-------------------------------------------------------------|-------------------|-----------------------------------------------------|
| task-cleanup SKILL.md    | 対象特定・ファイル確認・分類・統合・front matter 更新・削除・報告        | SDD_LANG, SDD_*, git | `plugins/sdd-workflow/skills/task-cleanup/SKILL.md`   |
| scope_confirmation       | 引数なし実行時の範囲確認提示の例                                  | -                 | `plugins/sdd-workflow/skills/task-cleanup/examples/`  |
| cleanup_output           | クリーンアップ結果出力の基底テンプレート（日英）                        | SDD_LANG          | `plugins/sdd-workflow/skills/task-cleanup/templates/{en,ja}/` |

---

# 5. データ構造

## 5.1. 統合／削除の分類基準（実装準拠）

**統合対象（→ `*_design.md`）**:

| カテゴリ           | 例                                          |
|:-----------------|:--------------------------------------------|
| 設計判断と根拠      | 「Redis 採用理由: ...」「このパターン採用理由: ...」   |
| 代替案評価結果      | 「Option A vs B の比較」「不採用案とその理由」        |
| 技術知見・Tips     | 実装中の発見・性能改善ポイント                       |
| トラブルシュート     | 遭遇した問題と解決策                              |
| 再利用パターン      | 他機能でも使えるコード／設計パターン                   |

**削除可能（移行不要）**:

| カテゴリ           | 例                                          |
|:-----------------|:--------------------------------------------|
| 作業進捗メモ        | 「X を実装中」「Y 完了」                          |
| 一時的な調査ログ     | 日記的内容・試行錯誤の記録                         |
| 具体的な実装手順     | コードに反映済みの詳細手順                          |
| タスク一覧          | 完了タスクのリスト                               |
| 日付依存情報        | 特定期間・日付に依存する情報                        |

## 5.2. 統合先決定ロジック（実装準拠）

```
統合対象あり:
  1. 内容に最も関連する既存 *_design.md を探す
  2. 適切な既存ファイルが無い場合:
     - 関連 *_spec.md が存在 -> 対応する *_design.md を新規作成
     - 関連 *_spec.md が無い -> 統合をスキップ（情報を削除）
```

## 5.3. front matter 更新（実装準拠）

| 対象                        | 更新内容                                            |
|:---------------------------|:--------------------------------------------------|
| design doc `impl-status`   | 全タスク成功時に `"implemented"` へ                    |
| design doc `updated`       | 現在日付へ                                           |
| spec `status`              | 実装が仕様を裏付ける場合 `"approved"` を検討             |

---

# 6. ファイル構成

```
plugins/sdd-workflow/
├── skills/task-cleanup/
│   ├── SKILL.md                              # ユーザー呼び出しスキル本体（agent: haiku）
│   ├── examples/scope_confirmation.md        # 範囲確認提示の例
│   └── templates/{en,ja}/cleanup_output.md   # 出力基底テンプレート（日英）
└── .claude-plugin/plugin.json                # skills は "./skills" 参照で自動登録（T-002）
```

task-cleanup スキルは実装・登録済みであり、本設計書は逆算文書である。
新規追加ではないため plugin.json の変更は発生しない（既存登録の維持を確認する）。

---

# 7. 非機能要件実現方針

| 要件                     | 実現方針                                                                       |
|------------------------|------------------------------------------------------------------------------|
| NFR-001（安全性）        | 実装未完了は task/ を保持、統合先不明はユーザー確認。統合 → 削除の順序固定で統合前削除を防ぐ（DC_002） |
| NFR-002（多言語・一貫性）  | `SDD_LANG` に応じ `templates/{en,ja}/` を切り替え。日英で同等構成を維持（B-002）        |
| NFR-003（非冗長性）      | 移行元ファイル名等の履歴を残さず、既存 `*_design.md` と重複する内容は移行しない            |

---

# 8. テスト戦略

| テストレベル | 対象                              | カバレッジ目標                                        |
|:----------|:--------------------------------|:----------------------------------------------------|
| 構文検証    | `skills/task-cleanup/`           | plugin-lint（プロンプト Markdown 構文・命名規則）が通ること        |
| 手動検証    | デモンストレーション                  | 分類・統合・front matter 更新・統合後削除が順序どおり機能すること（FR-001〜005） |
| 整合性確認  | 統合後の `*_design.md`・front matter | 設計知見が自然に統合され履歴が残らないこと（NFR-003）              |

---

# 9. 設計判断

## 9.1. 決定事項

| 決定事項            | 選択肢                        | 決定内容                              | 理由                                                          |
|-------------------|-----------------------------|-------------------------------------|---------------------------------------------------------------|
| 実行モデル          | 既定モデル / haiku            | `agent: haiku`                       | 選別・統合は判断を要するが定型度が高く、軽量モデルでコスト効率を優先          |
| 削除方式            | `rm` / `git rm`               | `git rm`（`-r` でディレクトリ）          | Git 管理下で削除し履歴追跡・取り消しを可能にする                        |
| 削除順序            | 任意 / 統合完了後に固定          | 統合 → front matter 更新 → 削除の順     | 統合前削除の禁止（DC_002 / D-003）をプロセス順序として担保               |
| 統合先が無い場合     | 常に新規作成 / 条件分岐          | spec があれば新規 design 作成、無ければ削除 | 孤立した設計書の乱造を避けつつ、根拠ある知見のみ永続化する                  |
| 引数なし時の安全策    | 即実行 / 範囲確認               | 範囲確認でユーザー承認を得る             | task/ 全体削除の誤操作を防ぐ（NFR-001）                              |
| 履歴表記            | 残す / 残さない                | 残さない                             | 設計書を成果物として簡潔に保ち、移行痕跡でノイズを増やさない（NFR-003）        |

## 9.2. 未解決の課題

| 課題                                   | 影響度 | 対応方針                                          |
|--------------------------------------|-----|---------------------------------------------------|
| 統合対象／削除可能の判定の基盤モデル依存    | 中   | 分類基準表を精緻化。判断困難時はユーザー確認へフォールバック        |
| 複数機能にまたがる知見の統合先選定         | 低   | 最も関連する設計書へ統合する方針を明記                        |

---

# 10. 原則準拠チェックリスト

| 原則ID  | 原則名                       | 準拠状況 | 備考                                                       |
|-------|-----------------------------|--------|------------------------------------------------------------|
| A-001 | Skills-First                 | ✅     | `skills/task-cleanup/` として実装（legacy commands 不使用）      |
| B-002 | 多言語対応（EN/JA）の一貫性     | ✅     | `templates/{en,ja}/` と `SDD_LANG` による出力言語切り替え          |
| D-001 | Specification-Driven          | ✅     | 設計知見を `*_design.md` へ集約し仕様・設計を真実の源に保つ            |
| D-003 | ドキュメント永続性ルールの遵守   | ✅     | 統合完了後にのみ task/ を削除し、統合前削除を発生させない              |
| T-002 | plugin.json 登録の徹底         | ✅     | `./skills` 参照で自動登録済み                                   |
| T-003 | 日本語出力の文字化け防止         | ✅     | 日本語テンプレート・本設計書に U+FFFD / mojibake を含めない            |

**原則から逸脱する場合**: 理由を「9.1. 決定事項」に明記し、CONSTITUTION.md の例外プロセスに従うこと。
