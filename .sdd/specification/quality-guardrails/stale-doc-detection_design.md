---
id: "design-quality-guardrails-stale-doc-detection"
title: "ドキュメント更新漏れ検知"
type: "design"
status: "draft"
sdd-phase: "plan"
impl-status: "implemented"
created: "2026-07-08"
updated: "2026-09-02"
depends-on: ["spec-quality-guardrails-stale-doc-detection"]
tags: ["hooks", "consistency-check", "quality-gate"]
category: "quality-guardrails"
priority: "medium"
risk: "medium"
---

# ドキュメント更新漏れ検知

**関連 Spec:** [stale-doc-detection_spec.md](stale-doc-detection_spec.md)
**関連 PRD:** [stale-doc-detection.md](../../requirement/quality-guardrails/stale-doc-detection.md)（親: [quality-guardrails](../../requirement/quality-guardrails/index.md)）
**準拠する原則:** [CONSTITUTION.md](../../CONSTITUTION.md) A-002（フックとスクリプトの責務分離）, B-001（Vibe Coding 防止）, D-001（Specification-Driven）

---

# 1. 実装ステータス

**ステータス:** 🟢 実装済み

本設計書は既存実装（`scripts/post-tool-use.py` および `scripts/hook_common.py`）の挙動を逆算して記述した
ものである。検知トリガー・検知条件・警告内容は実装コードを真実の源とする。

## 1.1. 実装進捗

| モジュール/機能                | ステータス | 備考                                                          |
|------------------------------|--------|-------------------------------------------------------------|
| PostToolUse フックスクリプト     | 🟢     | `scripts/post-tool-use.py`（3 種の検知分岐 + 無介入）             |
| フック共通ヘルパー               | 🟢     | `scripts/hook_common.py`（stdin 解析・パス解決・additionalContext emit） |
| フック登録                      | 🟢     | `hooks/hooks.json` の `PostToolUse`（matcher: `Write\|Edit`）   |
| 回帰テスト                      | 🟢     | リポジトリルート `scripts/test-hook-scripts.sh`（3 分岐 + 無介入を検証。CI の `test` ジョブで実行） |

---

# 2. 設計目標

- ファイル編集後に**軽量・決定的**に更新漏れの可能性を判定し、応答性を阻害しない（NFR-001: 500ms 以内）
- 検知は**非ブロッキング**とし、`additionalContext` によって確認・同期を促すに留める（FR-004 / DC_001）
- ファイル種別（仕様書 / 要求仕様 / ソースコード）に応じて促す内容を切り替える（FR-001〜003）
- 更新漏れの可能性がない編集には一切介入しない（FR-005）
- 機械的なパス判定（フック）と判断・検証（検証スキル）の**責務を分離**する（A-002）

---

# 3. 実装方式

| 領域   | 採用方式                                | 選定理由                                                                        |
|------|-------------------------------------|-------------------------------------------------------------------------------|
| hook | Python 3 スクリプト（パス判定 + ファイル探索） | 決定的・軽量な判定であり Claude の推論を要さない。A-002 に従い機械的処理をスクリプトへ委譲し 500ms 要件を満たす |
| hook | `additionalContext` による非ブロッキング注入 | 編集を拒否せず AI へ促しを渡すのに適合（DC_001）。`deny` は使わない                          |
| 実装同期 | `pathlib.Path.rglob` による spec 探索（`{stem}_spec.md` → `{stem}.md`） | ソースの basename から対応する抽象仕様書を階層構造を問わず発見する。spec がある場合のみ同期を促す。技術設計書は `task/{ticket-number}/design-draft.md` の一時ドラフトのため追随先にしない |

本機能は検証・修正を Claude や検証スキル（doc-consistency-checker / `/check-spec`）に委ね、フックは
「更新漏れの可能性の可視化」までを担う。

---

# 4. アーキテクチャ

## 4.1. システム構成図

```mermaid
graph TD
    E[ファイル編集 Write/Edit] --> RT[フックランタイム]
    RT -->|stdin JSON| PTU[post-tool-use.py]
    PTU -->|read_stdin_json / relative_to_project| HC[hook_common.py]
    PTU -->|load_sdd_paths| CFG[.sdd-config.json / 既定値]
    PTU --> D{ファイル種別判定}
    D -->|.sdd/specification/*.md| C1[整合性確認を注入]
    D -->|.sdd/requirement/*.md| C2[下流伝播確認を注入]
    D -->|.sdd/adr/*.md| C4[追記専用+spec反映確認を注入]
    D -->|.sdd 配下その他| S1[return 無出力]
    D -->|ソース拡張子| W[find_spec_doc: rglob]
    W -->|spec あり| C3[spec 同期を注入]
    W -->|spec なし| S2[無出力]
    C1 & C2 & C3 & C4 -->|additionalContext| CL[Claude]
```

## 4.2. モジュール分割

| モジュール名           | 責務                                                                            | 依存関係            | 配置場所                                          |
|---------------------|-------------------------------------------------------------------------------|-------------------|-------------------------------------------------|
| post-tool-use.py    | 編集ファイルパスから種別を判定し、更新漏れの可能性に応じ additionalContext を emit（検知のみ・非ブロッキング） | hook_common.py, doc_walker.py, pathlib, sys | `plugins/sdd-workflow/scripts/post-tool-use.py`   |
| DOC_REMINDERS       | `.sdd/` 配下の種別ごとの `(プレフィックス属性名, 索引更新の有無, メッセージ)` を並べたテーブル。分岐を宣言的に保持する | -                 | `post-tool-use.py` 内のモジュール定数                |
| find_spec_doc       | 仕様書ディレクトリ配下を `rglob` し、`{stem}_spec.md` → `{stem}.md` の順に最初に一致した spec のパスを返す（なければ空文字） | pathlib           | `doc_walker.py`（`post-tool-use.py` から利用）       |
| hook_common.py      | stdin JSON 解析・プロジェクトルート解決・`.sdd` パス解決・additionalContext emit の共通ヘルパー | json, sys, os      | `plugins/sdd-workflow/scripts/hook_common.py`      |
| hooks.json          | `PostToolUse`（matcher `Write\|Edit`）へのスクリプト登録                            | -                 | `plugins/sdd-workflow/hooks/hooks.json`            |

---

# 5. 検知ロジック

## 5.1. 判定順序と検知条件

`post-tool-use.py` は編集ファイルの相対パス（`rel_path`）を求め、以下の順に判定する。最初に一致した分岐で
`additionalContext` を emit して `return` する（早期リターン）。

| 順序 | 検知条件                                                        | 動作                                       | 対応 FR |
|----|---------------------------------------------------------------|-------------------------------------------|--------|
| 0  | `file_path` が空 / プロジェクト外                                 | 何もしない（return）                         | -      |
| 1  | `.sdd/specification/` 配下かつ `.md`                             | PRD ↔ spec ↔ adr の整合性確認を注入           | FR-001 |
| 2  | `.sdd/requirement/` 配下かつ `.md`（PRD）                        | 下流 spec への変更伝播確認を注入               | FR-002 |
| 3  | `.sdd/adr/` 配下かつ `.md`（決定ログ）                            | 追記専用の原則と spec 反映確認を注入            | FR-006 |
| 4  | `.sdd/` 配下のその他                                             | 何もしない（return）                         | FR-005 |
| 5  | ソース拡張子（`SOURCE_EXTENSIONS`）かつ対応 spec あり              | spec 同期を注入                              | FR-003 |
| 6  | 上記いずれにも該当しない（対応 spec なし等）                         | 何もしない                                   | FR-005 |

`.sdd/` 配下の判定は `DOC_REMINDERS` テーブルを回す `_process_sdd_doc` に閉じ込め、「該当なしの
`.sdd/` ファイルは無出力」という catch-all はそのループ**後**に置く。これによりディレクトリ種別を追加する
際に「catch-all より前に置く」ことを人間が覚えている必要がなくなる（順序制約を構造で保証する）。
ソースファイルの処理は `_process_source_file` に分離する。

`.sdd` パス（`sdd_root` / `requirement_dir` / `specification_dir` / `adr_dir`）は `load_sdd_paths` により
解決され、`.sdd-config.json` の `directories.{requirement,specification,adr}` があればその設定を、なければ
既定値（`.sdd` / `requirement` / `specification` / `adr`）を用いる。フックは環境変数に依存せず
`.sdd-config.json` を直接読むため、セッション開始時に書き出される `SDD_ADR_DIR` / `SDD_ADR_PATH`
（スキル・テンプレート向け）とは同じ設定値を独立に解決する関係にある。

## 5.2. ソース → 抽象仕様書の対応付け（find_spec_doc）

ソースコード編集時は、編集ファイルの拡張子を除いた basename（`stem`）を用いて、仕様書ディレクトリ配下を
`rglob` で走査し `{stem}_spec.md` → `{stem}.md` の順に spec を探索する。発見した場合のみ spec 同期を促す。

- 対応付けは basename ベースのため、ディレクトリ階層（フラット / 階層構造）を問わず発見できる
- サフィックス付き（`{stem}_spec.md`）を優先し、次にサフィックスなし（`{stem}.md`）を探す。
  `{stem}_design.md` は spec ではないため一致しない
- 同名候補が複数ある場合はパス文字列順で最初の 1 件を返す（決定的な結果を保証する）
- 仕様書ディレクトリが存在しない場合（未初期化プロジェクト）は探索せず無出力

## 5.3. 警告内容（additionalContext）

いずれの分岐も `emit_additional_context("PostToolUse", <text>)` で以下の JSON を emit する。
`ensure_ascii=False` により、パスに含まれる日本語も UTF-8 のまま保持する（T-003）。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "<検知分岐に応じたメッセージ>"
  }
}
```

| 分岐   | メッセージ要旨（英語で注入）                                                                        |
|------|------------------------------------------------------------------------------------------|
| 仕様書 | `'<rel_path>' was updated.` PRD ↔ spec ↔ adr（要求 ID 参照・データモデル・API 定義）の整合性確認と doc-consistency-checker スキルの実行を促す |
| PRD  | `'<rel_path>' (PRD) was updated.` 下流 spec への変更伝播（新規・変更された UR/FR/NFR）の確認と doc-consistency-checker スキルの実行を促す |
| adr  | `'<rel_path>' (ADR) was updated.` 追記専用（過去エントリを書き換えない）の確認と、決定が spec に反映されているかの確認を促す |
| ソース | `'<rel_path>' was updated and a matching specification '<spec_rel>' exists.` 公開 API・データモデル・振る舞いが変わった場合の spec 更新（真実の源の維持）と `/check-spec` を促す |

---

# 6. ファイル構成

```
plugins/sdd-workflow/
├── scripts/
│   ├── post-tool-use.py    # PostToolUse フック本体（種別判定・検知ロジック）
│   └── hook_common.py      # stdin 解析・パス解決・additionalContext emit 共通ヘルパー
└── hooks/
    └── hooks.json          # PostToolUse（matcher: Write|Edit）へフックを登録
```

本機能はプラグインルートの `hooks.json` にフックが登録済みであり、新規スキル・エージェント追加ではないため
`plugin.json` の変更は不要（T-002）。

なお回帰テスト `scripts/test-hook-scripts.sh` は上記ツリー外の**リポジトリルート直下 `scripts/`** に配置され、
CI（`.github/workflows/ci.yml` の `test` ジョブ）から実行される。本設計書中の `scripts/` は文脈により
プラグイン配下（`plugins/sdd-workflow/scripts/`：フック本体）とリポジトリルート（テスト系）の 2 種を指すため注意する。

---

# 7. 非機能要件実現方針

| 要件                          | 実現方針                                                                                        |
|-----------------------------|-----------------------------------------------------------------------------------------------|
| NFR-001（500ms 以内）          | 外部プロセス・ネットワーク・LLM 呼び出しを行わず、標準ライブラリ（`os` / `json`）のみで同期処理する。ファイル探索は仕様書ディレクトリ配下の `os.walk` に限定する |
| NFR-002（クロスプラットフォーム）   | POSIX 準拠の Python 3。パス区切りは `os.sep` / `os.path` を用い、ファイル探索も `os.walk` で macOS・Linux 双方で動作する |
| NFR-003（フックイベント仕様準拠） | `hookSpecificOutput.additionalContext` 形式で emit。`deny` は使わず exit code 0 で正常終了する          |

---

# 8. テスト戦略

| テストレベル       | 対象                                        | カバレッジ目標                                                    |
|----------------|-------------------------------------------|----------------------------------------------------------------|
| 回帰テスト（hook） | リポジトリルート `scripts/test-hook-scripts.sh` | spec 編集の整合性確認・PRD 編集の下流伝播・対応 design ありソース編集の同期・対応 design なしソース編集の無介入の 4 ケース |
| CI 検証          | `.github/workflows/ci.yml` の `test` ジョブ   | フックスクリプト回帰テストが CI で実行される                              |
| 手動検証         | デモンストレーション                            | ファイル編集後の体感遅延がない水準（NFR-001）                             |

---

# 9. 設計判断

## 9.1. 決定事項

| 決定事項            | 選択肢                                | 決定内容                          | 理由                                                                 |
|------------------|--------------------------------------|---------------------------------|--------------------------------------------------------------------|
| 検知の実装層         | フック（Python）/ スキル（LLM）           | パス判定はフックに実装             | A-002。決定的なパス判定を LLM に委ねるとトークン浪費・応答遅延を招く              |
| ブロッキング可否      | deny でブロック / 非ブロッキング注入        | 非ブロッキング（additionalContext） | DC_001。編集後の更新漏れは警告に留め、修正判断は開発者と AI に委ねる               |
| 検証の責務          | フックで整合性を検証 / 促しのみ            | 促しのみ（検証は検証スキルへ誘導）    | 子 PRD スコープ外（実際の整合性検証は doc-consistency-checker 等が担う）        |
| ソース → 設計書の対応 | パスマッピング表 / basename で walk 探索   | basename で `os.walk` 探索        | 階層構造・フラット構造の双方で対応設計書を発見でき、設定不要                       |
| 検知なし時の挙動      | 常に何か出力 / 無出力                     | 該当なしは return し無出力          | FR-005。無関係な編集にノイズを出さず開発フローに介入しない                      |
| 出力エンコーディング   | `ensure_ascii=True` / `False`         | `ensure_ascii=False`（UTF-8）      | T-003。パスに含まれる日本語を additionalContext に文字化けなく含める            |

## 9.2. 未解決の課題

| 課題                                       | 影響度 | 対応方針                                                       |
|------------------------------------------|-----|-------------------------------------------------------------|
| basename 衝突（同名 stem の複数ソース）で誤った spec を提示する可能性 | 低   | パス文字列順で最初に発見した spec を用いる。厳密なパス対応は将来検討   |
| パス規約から外れた配置のドキュメントは検知対象外            | 低   | パス判定ベースの設計上の制約。命名・配置規約は naming-enforcement で担保 |

---

# 10. 原則準拠チェックリスト

| 原則ID  | 原則名                    | 準拠状況 | 備考                                                        |
|-------|--------------------------|--------|-----------------------------------------------------------|
| A-002 | フックとスクリプトの責務分離     | ✅     | 機械的なパス判定は Python フック、整合性検証は検証スキルに分離           |
| B-001 | Vibe Coding 防止          | ✅     | 更新漏れによる仕様・実装の乖離を編集直後に検知・可視化する                 |
| D-001 | Specification-Driven      | ✅     | 関連ドキュメント（PRD / spec / design）の同期を促し真実の源を維持する    |
| T-002 | plugin.json 登録の一貫性     | ✅     | 既存フックの逆算記述であり新規コンポーネント追加なし（plugin.json 変更不要） |
| T-003 | 日本語出力の文字化け防止        | ✅     | `ensure_ascii=False` でパス中の日本語を保持                       |
