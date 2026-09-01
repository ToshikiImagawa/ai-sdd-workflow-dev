---
id: "prd-quality-guardrails-naming-enforcement"
title: "ファイル命名規則の強制"
type: "prd"
status: "draft"
created: "2026-07-07"
updated: "2026-09-01"
depends-on: ["prd-quality-guardrails"]
tags: ["hooks", "naming-convention", "quality-gate"]
category: "quality-guardrails"
priority: "medium"
risk: "medium"
---

# ファイル命名規則の強制 要求仕様書

## 概要

本ドキュメントは、品質ガードレール機能群のうち **`.sdd/` 配下のファイル命名規則の強制**に対する要求仕様書である。
親 PRD は [index.md](index.md) を参照。

`.sdd/` 配下のドキュメントは命名規則（`requirement/` はサフィックスなし必須）によって種別が識別される。
`specification/` は単一種別ディレクトリ（配下は抽象仕様書のみ）であり、ディレクトリ自体が種別を表すため
`_spec.md` サフィックスは任意とする（設計書は `task/{ticket-number}/design-draft.md`・`adr/{feature}.md`
へ移管済みで `specification/` 配下には存在しない。`-decisions` サフィックス付きファイル名は既存ファイルの
みで有効な旧表記）。命名規則違反（`requirement/` へのサフィックス付与）はワークフロー全体の整合性を損なう
ため、違反ファイルの書き込みをフックで構造的にブロックし、プロジェクト原則（[CONSTITUTION.md](../../CONSTITUTION.md)
D-002: ファイル命名規則の厳守）の遵守を強制する。

---

# 1. 要求図の読み方

SysML 要求図の記法（要求タイプ・リスクレベル・検証方法・関係タイプ）の凡例は
[PRD_TEMPLATE.md](../../PRD_TEMPLATE.md) のセクション 1 を参照。

---

# 2. 要求一覧

## 2.1. ユースケース図

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    ClaudeCode((Claude Code))
    HookRuntime((フックランタイム))

    subgraph NamingEnforcement["ファイル命名規則の強制"]
        WriteFile([ファイルを書き込む])
        ValidateNaming([命名規則を検証しブロックする])
    end

    ClaudeCode --- WriteFile
    ValidateNaming -.->|"<<拡張>>"| WriteFile
    HookRuntime -.->|"イベント発火"| ValidateNaming
```

## 2.2. 機能一覧（テキスト形式）

- ファイル命名規則の強制
    - `.sdd/` ファイル命名規則の検証とブロック

---

# 3. 要求図（SysML Requirements Diagram）

```mermaid
%%{init: {'theme': 'dark'}}%%
requirementDiagram
    functionalRequirement NamingEnforcement {
        id: FR_001
        text: "sdd配下の命名規則違反の書き込みをブロックする"
        risk: medium
        verifymethod: test
    }
```

本ファイルの FR_001 は [index.md](index.md) の UR_004（プロジェクト原則の自動遵守）から派生する
（親 PRD の全体要求図では FR_002 として定義）。
関連する横断要求・制約として、index.md の NFR_001（フック処理の軽量性）・IR_001（フックイベント仕様への準拠）・
DC_001（ブロッキングの最小化。deny によるブロックは本機能の命名規則違反のみに限定）・
DC_004（クロスプラットフォーム対応）が本機能に trace する。

---

# 4. 要求の詳細説明

## 4.1. 機能要求

### FR_001: ファイル命名規則の強制

`.sdd/` 配下へのファイル書き込み・編集時に命名規則を検証し、違反時は書き込みをブロックする。
[index.md](index.md) の UR_004 から派生。

**トリガー方式:** 自動（`.sdd/` 配下へのファイル書き込み・編集前のフック）

- `requirement/` 配下: `_spec` / `_design` サフィックスの付与を禁止
- `specification/` 配下: サフィックスの有無を問わずブロックしない。単一種別ディレクトリのため
  ディレクトリ自体で種別を識別できる（`_spec.md` は任意）。設計書は `task/{ticket-number}/design-draft.md`
  （一時）または `adr/{feature}.md`（永続）に配置され、`specification/` 配下には存在しない
- 違反時は JSON Decision Control（`permissionDecision: deny`）により理由付きでブロックする

**検証方法:** テストによる検証

---

# 5. 前提条件

- Claude Code のプラグイン機構・フックイベントシステムが利用可能であること
- 対象プロジェクトで sdd-workflow プラグインが有効化されていること

---

# 6. スコープ外

以下は本 PRD のスコープ外とします：

- プロンプト曖昧性の検知（[vibe-detection.md](vibe-detection.md) で扱う）
- 編集時のコンテキスト注入・編集後のリマインド（[constitution-injection.md](constitution-injection.md) /
  [stale-doc-detection.md](stale-doc-detection.md) で扱う）
- front matter の内容検証（[front-matter-validation.md](front-matter-validation.md) で扱う。本機能はファイル名のみを対象とする）
- `adr/` 配下の命名検証、および生成スキル（`task-cleanup` 等）が新規ファイル作成時にどちらの名前を使うかの
  デフォルト選択（`adr/` も `specification/` と同様の単一種別ディレクトリだが、本機能は現時点で `adr/` 用の
  検証対象プレフィックスを持たない。管理対象外パスとして常にブロックしないため、結果的にサフィックス任意という
  望む挙動には一致する。生成側の名前選択は各生成スキル自身の実装に委ねる。`adr/` 固有の検証が必要になった
  場合は別途検討する）
