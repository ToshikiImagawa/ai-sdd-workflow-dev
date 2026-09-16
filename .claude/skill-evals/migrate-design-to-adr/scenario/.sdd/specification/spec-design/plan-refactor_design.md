---
id: "design-spec-design-plan-refactor"
title: "リファクタリング計画"
type: "design"
status: "draft"
sdd-phase: "plan"
impl-status: "implemented"
created: "2026-07-08"
updated: "2026-09-02"
depends-on: ["spec-spec-design-plan-refactor"]
tags: ["refactoring", "reverse-engineering", "skill-implementation"]
category: "spec-design"
priority: "medium"
risk: "medium"
---

# リファクタリング計画 - 技術設計書

**関連 Spec:** [plan-refactor_spec.md](plan-refactor_spec.md)
**関連 PRD:** [plan-refactor.md](../../requirement/spec-design/plan-refactor.md)
**実装参照:** `plugins/sdd-workflow/skills/plan-refactor/SKILL.md`

---

# 1. 設計概要

## 1.0. 設計目標

- 技術設計書を非永続化し、`task/{ticket-number}/design-draft.md` のライフサイクルに一本化する
- Case 判定基準を「仕様書の有無」に統一し、設計書が永続化されなくても判定が破綻しないようにする
- 逆生成成果物を永続性で書き分け、永続すべき仕様書と破棄前提の設計ドラフトを混同しない
- 確定した決定のみを `adr/{feature-name}.md` に永続化し、未確定の計画が永続文書として残らないようにする

## 1.1. 現在のアーキテクチャ

`/plan-refactor` スキルは Claude Code プラグイン内でエージェント実行される。
実装の核は以下の2つのユースケースに分かれている：

- **Case A**: 既存仕様書がある場合、仕様と実装の比較から改善ポイントを特定し、リファクタリング計画を設計ドラフトに追加
- **Case B**: 仕様書もない場合、実装から仕様書を逆生成して永続化し、設計は一時ドラフトとして生成してから計画を作成

いずれの Case でも、設計とリファクタリング計画の書き込み先は
`${SDD_TASK_PATH}/{ticket-number}/design-draft.md`（一時ドラフト）であり、
`specification/` 配下に永続的な技術設計書を作成しない。

## 1.2. 技術スタック

- **言語**: Markdown（ドキュメント生成）/ Python（ファイル検索・スキャン: `python3` で実行）
- **実行環境**: Claude Code エージェント実行時
- **出力形式**: Markdown（front matter 付き）
- **テンプレートエンジン**: 環境変数置換 + プリミティブなテンプレート処理

---

# 2. アーキテクチャ

## 2.1. コンポーネント構造

```
plugins/sdd-workflow/skills/plan-refactor/
├── SKILL.md                      # スキル定義書（入出力・フロー・ルール）
├── scripts/
│   ├── scan-existing-docs.py    # Phase 1: 既存ドキュメント検索（python3 実行）
│   └── find-implementation-files.py  # Phase 2: 実装ファイル検索（python3 実行）
├── templates/{en,ja}/
│   ├── reverse_spec_template.md    # Case B: 逆生成仕様書テンプレート
│   ├── reverse_design_template.md  # Case B: 逆生成設計ドラフトテンプレート
│   ├── refactor_plan_section.md    # Both: リファクタリング計画テンプレート
│   └── completion_output.md        # 出力フォーマット
├── examples/
│   ├── cli_usage.md             # 使用例
│   ├── case_a_existing_docs.md  # Case A のワークスルー
│   └── case_b_no_docs.md        # Case B のワークスルー
└── references/
    ├── front_matter_spec_design.md     # front matter スキーマ定義
    ├── design_doc_integration.md       # 設計ドラフト統合ガイド
    └── refactor_patterns.md            # リファクタリングパターン集
```

## 2.2. データフロー

```
ユーザー入力
  ↓
[フェーズ 1: 事前チェック]
  - チケット番号を解決（--ticket / AskUserQuestion / --ci では必須）
  - scan-existing-docs.py → .sdd/.cache/plan-refactor/existing-docs.json
  - Case A / Case B 判定（仕様書の有無が基準）
  ↓
[フェーズ 1.5: ユーザー意図の解析]
  - context パラメータを解析（オプション）
  ↓
[フェーズ 2: 実装ファイル検出]
  - find-implementation-files.py → implementation-files.json
  - ファイル数チェック（20+ の場合、ユーザー確認）
  - 実装ファイルを読み込む
  ↓
[フェーズ 3: 処理分岐]
  ├─ Case A:
  │   - 既存仕様書を読み込む（設計ドラフト・旧永続設計書があれば補助入力）
  │   - 実装と仕様の比較分析
  │   - 設計ドラフトにリファクタリング計画を生成・追記
  │
  └─ Case B:
      - 仕様書テンプレートから逆生成 → specification/ に永続化
      - 設計テンプレートから逆生成 → task/{ticket-number}/design-draft.md
      - 設計ドラフトにリファクタリング計画を生成・追記
  ↓
[フェーズ 4: 検証]
  - 必須セクション確認
  ↓
[フェーズ 5: 次のステップ]
  - レビューエージェント推奨
  - 決定ログ（adr/）への統合導線を提示
  ↓
出力: 設計ドラフト（+ Case B は逆生成仕様書）+ リファクタリング計画
```

---

# 3. 実装詳細

## 3.1. Phase 1: Pre-flight Checks

### Step 1.0: Resolve Ticket Number

設計ドラフトのパスはチケット単位でスコープされるため、**Step 1.1 のスキャンより前に**チケット番号を確定させる。

- `--ticket=<number>` 指定あり → その値を使用
- 省略かつ非 CI モード → `AskUserQuestion` で確認してから Step 1.1 へ進む
- 省略かつ `--ci` モード → エラーとして中断（対話的に確認できないため）

Step 1.1 より前に確定させないと、スキャン時点で `design_draft_exists` を判定できず、
既存ドラフトを Case A の補助入力として読み込めない。

### Step 1.1: Scan for Existing Documents

**実装ファイル**: `scripts/scan-existing-docs.py`

**引数**: `<feature-name> [ticket-number]`

**処理**:
1. `.sdd/requirement/{feature-name}.md` → PRD を検索
2. `.sdd/specification/{feature-name}_spec.md` → 仕様書を検索。存在しない場合はサフィックス無しの
   `.sdd/specification/{feature-name}.md` も検索する（`specification/` は単一種別ディレクトリのため
   `_spec` サフィックスは任意）
3. `.sdd/task/{ticket-number}/design-draft.md` → 設計ドラフトを検索（`ticket-number` 指定時のみ）
4. `.sdd/specification/{feature-name}_design.md` → 旧永続設計書（v4.x 由来）を検索。Case 判定には使わず、
   移行途中のプロジェクトで補助入力として提示するためだけに検出する
5. 階層構造対応：親機能ディレクトリ内のファイルも検索
6. 結果を `.sdd/.cache/plan-refactor/existing-docs.json` に出力

**出力例**:
```json
{
  "prd_exists": true,
  "prd_path": ".sdd/requirement/auth.md",
  "spec_exists": true,
  "spec_path": ".sdd/specification/auth_spec.md",
  "design_draft_exists": false,
  "design_draft_path": "",
  "legacy_design_exists": false,
  "legacy_design_path": "",
  "structure": "flat",
  "feature_name": "auth",
  "ticket_number": "91",
  "case": "A"
}
```

### Step 1.3: Determine Processing Case

- `spec_exists == true` → **Case A** (既存仕様書を土台にする)
- `spec_exists == false` → **Case B** (仕様書から逆生成)

判定は仕様書の有無のみで行い、`specification/*_design.md` の存在には依存しない
（技術設計書は永続文書ではないため、有無が判定基準として成立しない）。
`design_draft_exists` が `true` の場合、既存ドラフトを Case A の補助入力として読み込む。

## 3.2. Phase 1.5: Parse User Intent (Optional)

**入力**: `context` パラメータ（例: "無限スクロール化してパフォーマンス改善"）

**処理**:
- パラメータがある場合、プロンプトで Claude に解析させる
- 抽出項目:
  - Primary Goal: 達成したい主要な改善
  - Motivation: なぜそれが必要か
  - Approach: 使用する技術・パターン（オプション）

**利用先**:
- リファクタリング計画の "Purpose and Background" セクションで優先度付け
- "Refactoring Strategy" で指定の手法を採用
- "Business/Technical Drivers" で motivation を記載

## 3.3. Phase 2: Implementation Discovery

### Step 2.1: Find Implementation Files

**実装ファイル**: `scripts/find-implementation-files.py`

**処理**:
1. `feature-name` をパターンマッチング
   - ファイル名に `{feature-name}` を含む
   - ファイル内容に `{feature-name}` を含む（grep）
2. `--scope=<dir>` で検索範囲を限定（指定時）
3. 除外パターン: `node_modules/`, `.git/`, `dist/`, `build/`, `*.test.*`
4. 結果を `.sdd/.cache/plan-refactor/implementation-files.json` に出力

**出力例**:
```json
{
  "feature": "auth",
  "file_count": 12,
  "files": [
    {
      "path": "src/services/auth.ts",
      "relevance": "high",
      "matches": ["function authenticate", "class AuthService"]
    }
  ]
}
```

### Step 2.3: Validate File Count

- ファイル数 > 20 かつ `--ci` フラグなし → ユーザー確認ダイアログ
- 選択肢: Yes / No / Adjust Scope
- Adjust Scope 選択時 → 新しいスコープを入力させる

### Step 2.4: Read Implementation Files

- `implementation-files.json` から最大10ファイルを優先度順に読み込む
- 優先度: ファイル名の関連度 > ファイルサイズ
- テストファイルは除外（初期読み込み時）

## 3.4. Phase 3A: Case A - Existing Specification

### Step 3A.2: Analyze Implementation vs. Specification

**比較観点**:
1. 仕様書（および設計ドラフトがあればそのコンポーネント記述）に記載された要素が実装に存在するか
2. 実装が仕様・設計に従っているか
3. 実装に存在するが仕様書に記載されていない部分があるか

**抽出内容**:
- **一致度**: ✓ 完全一致 / ⚠ 部分一致 / ✗ 乖離
- **乖離内容**: 技術スタック・API・データフロー・エラー処理
- **技術的負債**: コード重複・密結合・テストカバレッジ不足

### Step 3A.4: Generate Refactoring Plan

**テンプレート**: `templates/${SDD_LANG}/refactor_plan_section.md`

**セクション構成**:

| セクション | 内容 | 必須 |
|----------|------|------|
| Purpose and Background | リファクタリングの目的・背景。context がある場合は優先度付け | ✓ |
| Current State Analysis | 現状の問題点・メトリクス・根本原因。context に関連する項目を強調 | ✓ |
| Refactoring Strategy | 目標・アプローチ・トレードオフ。context の approach を採用すれば記載 | ✓ |
| Migration Plan | 段階的タスク・見積もり・依存関係 | ✓ |
| Impact Analysis | 破壊的変更・影響コンポーネント・ロールバック計画 | ✓ |
| Testing Strategy | ユニットテスト・統合テスト・E2E テスト計画 | ✓ |
| Success Criteria | メトリクス・受け入れ基準 | ✓ |
| Risks and Mitigations | リスク・軽減策 | ✓ |
| Timeline and Milestones | スケジュール・マイルストーン | - |

**例（context: "無限スクロール化してパフォーマンス改善"）**:

このコンテクストを使用した場合、生成される リファクタリング計画は以下のようになります（SDD_LANG=JA の場合）：

```markdown
## リファクタリング計画

### 目的と背景
現在のリスト表示は全アイテムを一度に DOM にレンダリングしているため、
1000+ アイテムで レンダリング時間が 3 秒以上かかる。
これを無限スクロール実装により 500ms 以下に改善する。

### 現状分析
- 全アイテムのデータを メモリに保持（20MB+）
- 初期ロード時に全 DOM を作成（実装: UserList.tsx:45）
- スクロールイベントの処理なし

### リファクタリング戦略
**アプローチ**: react-window による仮想化
- 動的にビューポート内のアイテムのみレンダリング
- メモリ使用量を 2MB 以下に削減
- 初期ロードを 200ms 以下に短縮

...
```

### Step 3A.5: Update Design Draft

**処理**: `${SDD_TASK_PATH}/{ticket-number}/design-draft.md` の末尾に
"## Refactoring Plan" セクションを追記する。ドラフトが未作成の場合は
`reverse_design_template.md` を土台に新規作成してから追記する。

**前提**: 既に "## Refactoring Plan" が存在する場合は置換。
旧永続設計書（`specification/*_design.md`）が残っているプロジェクトでも、そのファイルは編集せず
参照のみに使う（永続設計書を再生産しない）。

## 3.5. Phase 3B: Case B - No Specification (Reverse Engineering)

### Step 3B.1: Reverse-Engineer Specification

**テンプレート**: `templates/${SDD_LANG}/reverse_spec_template.md`

**抽出内容**:

| 項目 | 説明 | 実装参考箇所 |
|-----|------|-----------|
| **Feature Name** | 機能の識別子 | パラメータから |
| **Background** | なぜこの機能が必要か | コミットメッセージ / issue / コード内コメント |
| **Purpose** | 機能の目的 | 実装の主要 API / エクスポート |
| **Functional Requirements** | 何ができるのか | 公開 API / インターフェース定義 |
| **Data Model** | データ型・エンティティ | 型定義 / データベーススキーマ |
| **Behavior** | 主要なユースケース・フロー | 実装の核となるアルゴリズム |

**生成規則**:
```markdown
---
id: "spec-{feature-name}"
title: "{FEATURE_NAME}"
type: "spec"
status: "review"           # 逆生成は review 状態
sdd-phase: "specify"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
depends-on: ["prd-{feature-name}"]  # PRD があれば指定
tags: ["reverse-engineered"]
---

> **⚠️ 注意**: この仕様書は{DATE}時点の実装から逆生成されたものです。
> 元々の設計ではなく、現在の実装の文書化です。内容を確認の上、
> 必要に応じて更新してください。
```

### Step 3B.3: Reverse-Engineer Design Document

**テンプレート**: `templates/${SDD_LANG}/reverse_design_template.md`

**抽出内容**:

| 項目 | 説明 | 実装参考箇所 |
|-----|------|-----------|
| **Architecture Overview** | 高レベルアーキテクチャ | ディレクトリ構造 / モジュール設計 |
| **Component Structure** | コンポーネント一覧 | ファイル / クラス / 関数構成 |
| **Data Flow** | データの流れ | 呼び出し関係 / イベントハンドリング |
| **Key Algorithms** | 重要なアルゴリズム | 複雑な処理・計算ロジック |
| **API Design** | インターフェース設計 | 公開関数・エンドポイント・型定義 |
| **Error Handling** | エラー処理戦略 | 例外処理 / エラーコード |
| **Testing Strategy** | テスト構成 | テストファイル有無・カバレッジ |
| **Technical Debt** | 観測された負債項目 | コード重複・硬い結合・古いパターン |

**書き込み先**: `${SDD_TASK_PATH}/{ticket-number}/design-draft.md`（一時ドラフト）

**生成規則**:
```markdown
---
id: "design-{ticket-number}"   # チケット単位のドラフトパスに合わせる
title: "{FEATURE_NAME}"
type: "design"
status: "review"            # 逆生成は review 状態
sdd-phase: "plan"
impl-status: "implemented"  # 既に実装済み
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
depends-on: ["spec-{feature-name}"]
tags: ["reverse-engineered"]
---

> **⚠️ 注意**: この設計ドラフトは{DATE}時点の実装から逆生成されたものです。
> 現在の状態を文書化したものであり、元々の設計ではありません。
> 実装完了後に破棄される一時文書であり、確定した決定は決定ログへ統合してください。
```

### Step 3B.5: Generate Refactoring Plan

Case A と同じ流れで、設計ドラフトに「## Refactoring Plan」セクションを作成・追記

## 3.6. Phase 5: 決定ログへの導線

設計ドラフトは実装完了後に破棄されるため、リファクタリング計画で確定した決定
（採用した戦略・却下した代替案・トレードオフ）は `${SDD_ADR_PATH}/{feature-name}.md` へ
追記して永続化する。この統合は `/task-cleanup` が担い、本スキルは完了出力で導線を提示するだけに留める
（本スキルが決定ログを直接書くと、実装で計画が変わった場合に未確定の決定が永続化されるため）。

---

# 4. テンプレート管理

## 4.1. テンプレートの場所と優先度

### テンプレート検索順序

1. **プロジェクト定義テンプレート** (最優先)
   - `.sdd/SPECIFICATION_TEMPLATE.md`
   - `.sdd/DESIGN_DOC_TEMPLATE.md`

2. **プラグイン言語別テンプレート**
   - `plugins/sdd-workflow/skills/plan-refactor/templates/${SDD_LANG:-en}/`

3. **フォールバック** (推奨されない)
   - プラグイン EN テンプレート

### front matter スキーマ

**Spec front matter**:
```yaml
id: "spec-{feature-name}"
type: "spec"
status: "draft" or "review"
sdd-phase: "specify"
depends-on: ["prd-{feature-name}"] or []
tags: ["reverse-engineered"] (if Case B)
```

**Design draft front matter**（`id` は機能名ではなくチケット番号を使う。
ドラフトのパスがチケット単位でスコープされるため、パスと識別子を一致させる意図的な規約）:
```yaml
id: "design-{ticket-number}"
type: "design"
status: "draft" or "review"
sdd-phase: "plan"
impl-status: "implemented" or "not-implemented"
depends-on: ["spec-{feature-name}"]
tags: ["reverse-engineered"] (if Case B)
```

---

# 5. エラーハンドリング

| 状況 | 対応 |
|-----|------|
| 実装ファイルが見つからない | ユーザーに feature-name を確認。`--scope` の指定を推奨 |
| 20+ ファイル検出 | CI モードでない場合、確認ダイアログ表示。スコープ調整を提案 |
| context が曖昧 | `AskUserQuestion` で Primary Goal / Motivation を確認 |
| チケット番号が未指定 | Step 1.0 で `AskUserQuestion` で確認。`--ci` モードではエラーとして中断（ドラフトの配置先が決まらないため） |
| 旧永続設計書（`specification/*_design.md`）を検出 | 補助入力として読むだけで編集しない。移行が未完了である旨と、決定を `adr/` へ移す手動移行手順（README の "Migration from v4.x"）をユーザーに案内する |
| PRD / 既存仕様書が複数存在 | 最新の mtime を持つものを採用 |
| テンプレートが見つからない | プラグイン EN テンプレートにフォールバック |

---

# 6. テスト戦略

## 6.1. ユニットテスト

- 対象スクリプト: `scan-existing-docs.py`（複数構造・サフィックス有無・設計ドラフト検出・Case 判定の正確性）、`find-implementation-files.py`（マッチング精度・除外パターン・スコープ絞り込み）
- 配置: `tests/test_plan_refactor_scripts.py`（`python3 -m pytest tests/` で自動収集される）
- 併せて §6.2 統合テスト・§6.3 マニュアルテストおよび CI の `plugin-lint` で担保する

## 6.2. 統合テスト

- Case A: 既存仕様書がある機能で実行 → 設計ドラフトの作成・更新を確認
- Case A: 既存設計ドラフトがある状態で実行 → ドラフトが補助入力として読まれることを確認
- Case B: 仕様書がない機能で実行 → 逆生成仕様書（`specification/`）と設計ドラフト（`task/`）の生成を確認
- context パラメータ付き実行 → 計画に反映されたか確認

## 6.3. マニュアルテスト

- 実際のプロジェクトで実行
- レビューエージェントで品質確認

---

# 7. 言語対応（SDD_LANG）

- **EN**: 英語テンプレート・出力
- **JA**: 日本語テンプレート・出力

テンプレートパス: `templates/${SDD_LANG:-en}/`

---

# 8. デプロイ・リリース

- プラグイン `sdd-workflow` の一部として配布
- スキル `.claude-plugin/plugin.json` に登録
- ドキュメント: `SKILL.md`, テンプレート, examples, references

---

# 9. 設計判断の記録

### Decision 1: Case A/B の分岐設計

**判断**: 既存仕様書の有無で異なる処理流を採用

**理由**:
- 既存仕様書がある場合、逆生成より既存仕様を土台にした分析が効率的かつ安全
- 仕様書がない場合、テンプレートから逆生成して明確な文書を作成

**代替案**:
- 常に逆生成 → 既存仕様書を上書きしてしまいデータ喪失のリスク
- 常に既存ドキュメント参照 → 仕様書が無い既存実装に対応不可

**トレードオフ**:
- ロジック複雑性 ↑ / 安全性・柔軟性 ↑

### Decision 2: context パラメータのオプション化

**判断**: context は必須でなくオプション

**理由**:
- 自動分析で一般的な改善提案も可能
- context を指定することでより焦点を絞った計画が作成可能
- ユーザーの使い勝手が向上

**実装上の複雑性**: context 有無で異なるプロンプトを用意

### Decision 3: 20+ ファイルチェック

**判断**: 実装ファイルが多い場合、ユーザー確認を必須に

**理由**:
- 分析時間の増加を予防
- 不要なファイル読み込みを避ける（--scope で最適化可能）

**代替案**:
- 固定値でフィルタリング → ユーザー意図を反映できない
- 常にすべて読む → スケール問題

### Decision 4: Case 判定基準を設計書の有無から仕様書の有無へ移行

**判断**: Case 判定を `specification/*_design.md` の有無ではなく仕様書の有無で行う

**理由**:
- 技術設計書は永続文書ではなくチケット単位の一時ドラフトになったため、
  「設計書が無い」は正常な状態であり判定基準として成立しない
- 判定基準を据え置くと常に Case B に落ち、逆生成が無条件に走ってしまう
- 仕様書は永続文書であり、「仕様が整備済みか」はリファクタリング計画の前提として意味を持つ

**代替案**:
- 設計ドラフトの有無で判定 → チケット単位のため、同一機能を別チケットで扱うと毎回 Case B になる
- Case B を廃止 → 「PRD は無いが実装がある」既存機能を仕様化する唯一の導線が失われる

**トレードオフ**:
- 判定に使うパスが増える（サフィックス有無の 2 通り）/ 新方針との整合性 ↑

### Decision 5: 逆生成成果物の永続性を分けて配置する

**判断**: 逆生成仕様書は `specification/` に永続化、逆生成設計とリファクタリング計画は
`task/{ticket-number}/design-draft.md` に一時配置する

**理由**:
- 仕様書（抽象的な「何を」）は実装のリファクタリングでは変わらないため永続化に値する
- 設計とリファクタリング計画（具体的な「どう」）はチケットに紐づく作業計画であり、
  実装完了時点で役目を終える
- 確定した決定のみを `adr/` に残すことで、古い計画が永続文書として残り続ける問題を避ける

**代替案**:
- 両方を永続化 → 新方針が非永続化した設計書を再生産してしまう
- 両方を一時ドラフト化 → 逆生成仕様書が実装完了時に失われ、仕様の整備が無駄になる

**トレードオフ**:
- チケット番号の入力が必要になる / ドキュメントのライフサイクルの一貫性 ↑

---

# 10. 今後の拡張

- **実行時挙動分析**: コードカバレッジツールとの連携で動的情報を補完
- **差分レポート生成**: 設計書と実装の差分を図示
- **マイグレーション支援**: リファクタリング計画の自動タスク化・実装テンプレート生成

---

# 参照

- **親 PRD**: [spec-design](../../requirement/spec-design/index.md)
- **AI-SDD 原則**: [AI-SDD-PRINCIPLES.md](../../AI-SDD-PRINCIPLES.md)
- **スキル SKILL.md**: [SKILL.md](../../../plugins/sdd-workflow/skills/plan-refactor/SKILL.md)
- **テンプレート**: [templates](../../../plugins/sdd-workflow/skills/plan-refactor/templates/)
