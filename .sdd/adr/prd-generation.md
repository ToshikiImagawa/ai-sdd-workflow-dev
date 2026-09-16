---
id: "adr-prd-generation"
title: "PRD 生成パイプライン 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-24"
updated: "2026-09-02"
sdd-version: "5.0.0"
depends-on: ["spec-prd-generation"]
tags: ["prd-generation", "usecase-diagram", "requirements-analysis", "sysml", "traceability"]
category: "prd-generation"
---

# PRD 生成パイプライン 決定ログ

## 2026-07-24 書き込み主体をオーケストレーターのみに限定する

- **Decision**: PRD ファイルへの書き込みはオーケストレーター（generate-prd）のみが行い、構成要素生成サブスキルは `disallowed-tools: Write, Edit, Bash` として書き込み不可にする。
- **Rationale**: 全スキルが書き込める構成では、サブスキルの誤動作で PRD が破壊され得る。書き込み主体を 1 つに絞ることで構造的に防げる（DC_001）。
- **Rejected alternatives**: 全スキルが書き込む — 誤動作による PRD 破壊を構造的に防げないため却下。

## 2026-07-24 構成要素生成サブスキルを context: fork で隔離する

- **Decision**: 構成要素生成サブスキルを `context: fork` + `agent` 指定で実行し、メインコンテキストから隔離する。
- **Rationale**: 生成の中間出力でメインコンテキストを汚さず、トークンを節約できる（PLUGIN_AGENTS.md の方針）。
- **Rejected alternatives**: メインコンテキストを共有する — 中間出力でコンテキストが汚れトークンを消費するため却下。

## 2026-07-24 モデルを用途別に選定する

- **Decision**: 図生成は haiku、要求抽出・統合・準拠レビューは sonnet を用い、エイリアス表記で世代追従させる。
- **Rationale**: 定型的な図生成は haiku で十分な品質が出る一方、判断を要する処理には sonnet が必要で、用途別選定がコストと品質を両立させる。
- **Rejected alternatives**: 全て sonnet — 定型的な図生成にも高コストのモデルを使うことになるため却下。

## 2026-07-24 準備処理を Python スクリプトに切り出す

- **Decision**: テンプレート・参照のロードを `prepare-prd.py`（Python 3 標準ライブラリ）で事前に行う。
- **Rationale**: テンプレート・参照ロードは決定的処理であり、スクリプト化することでトークンを節約し Claude を判断・生成に専念させられる（A-002 フックとスクリプトの責務分離）。
- **Rejected alternatives**: Claude が逐次ファイルを読み込む — 決定的処理にトークンを消費するため却下。

## 2026-07-24 テンプレートはプロジェクト優先・プラグイン既定フォールバックとする

- **Decision**: プロジェクトの `PRD_TEMPLATE.md` を優先し、存在しない場合のみ言語別のプラグイン既定テンプレートにフォールバックする。
- **Rationale**: プロジェクト固有のテンプレートを尊重する必要がある（DC_002）。
- **Rejected alternatives**: プラグイン既定に固定する — プロジェクト固有のテンプレートを無視することになるため却下。

## 2026-07-24 対話 / CI モードを単一スキル + フラグで分岐する

- **Decision**: 対話モードと CI モードを別スキルに分けず、`--ci` フラグによる単一スキル内の分岐とする。
- **Rationale**: 生成ロジックを共有したまま、非対話環境では質問と生成後レビューを省略できる（FR-009 / UR_004）。
- **Rejected alternatives**: 対話用・CI 用の別スキルにする — 生成ロジックが二重化するため却下。

## 2026-09-02 追記モードの ID 採番を Claude の読み取りで行う

- **Decision**: 追記モードにおける要求 ID の採番は、既存の要求図を Claude が読んで最大値 + 1 を算出する方式とする。
- **Rationale**: 追記対象は要求図というテキスト構造であり、決定的な数値計算ではなく既存ノードの解釈（プレフィックス判定・サブ ID 階層）を要するため、Python 化のメリットが薄い（FR-010）。
- **Rejected alternatives**: 専用スクリプトで ID をカウントする — テキスト構造の解釈が必要なため、スクリプト化の利点が得られず却下。

## 2026-09-02 追記モードの統合を finalize-prd に委譲する

- **Decision**: 追記モードでは generate-prd が直接テキスト編集するのではなく、既存 PRD 本文を finalize-prd に渡して統合を委譲する。
- **Rationale**: DC_001（書き込み主体の限定）を保ちつつ、「統合はサブスキルに委譲する」という既存の設計と一貫させられる（FR-010）。
- **Rejected alternatives**: generate-prd が直接テキスト編集する — 書き込み主体の限定と既存の委譲設計から外れるため却下。
