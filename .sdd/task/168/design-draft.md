---
id: "design-168"
title: "法則案の生成と承認フロー 設計ドラフト"
type: "design"
status: "draft"
sdd-phase: "plan"
impl-status: "not-implemented"
created: "2026-10-19"
updated: "2026-10-19"
sdd-version: "5.1.0"
depends-on: ["spec-task-implementation-laws-drafting"]
ticket: "168"
tags: ["laws", "bend", "drafting"]
category: "task-implementation"
---

# 法則案の生成と承認フロー 設計ドラフト（issue #168）

**関連 spec:** [laws-drafting_spec.md](../../specification/task-implementation/laws-drafting_spec.md)

## 決定ログ

clarify Q1〜Q6 として提示し、2026-10-19 にオーナーが承認した（すべて推奨案）。

| Q | 決定 |
|:--|:--|
| Q1 | 判定表・集約規則・状態遷移と、制約事項・不変条件・数値目標のうち機械的に等式化できるものだけを抽出。法則化しない理由を生成物に残す |
| Q2 | 新規スキル `/draft-laws`（仮称） |
| Q3 | 既定上限 10（`.sdd-config.json` の `laws.max_laws`）。優先順は判定表の単調性・順序 > 集約 > 不変条件 > 数値境界。超過分は「未採用の候補」 |
| Q4 | 1 スキルに 3 段階。`laws-status` と 1 対 1。承認行が有効（ハッシュ一致）でなければ model/proof を拒否。承認行は AI が書かない |
| Q5 | post-tool-use の促し + 本文側の `# source:` 出典コメント + `bend` 不要の静的チェック |
| Q6 | 新 spec `laws-drafting_spec.md` + 既存 adr に追記。PRD は変更せず提案のみ。検収は第 1 弾 5 法則の再現 |

## 設計上の要注意点

1. **内容ハッシュと spec 変更の関係**: ハッシュは `LAWS.bend` 本文のみが対象で、spec が変わっても承認は自動失効しない。
   「spec 変更で承認失効」は、出典コメント（節ハッシュ）を更新して本文が変わったときに起こる。検出は静的チェックと促しで行う（spec §8）。
2. **出典コメントの置き場所**: 先頭コメント部は内容ハッシュ対象外なので、出典は `import` より後の法則直前に置く（spec §4.1）。
3. **`model` 段階は `LAWS.bend` を変更しない**: 誤りを見つけたら指摘に留める。変更すればハッシュが変わり承認が失効する。
4. **`draft` 再実行**: 承認行を持つ `LAWS.bend` は上書きせず差分を報告する。
5. **spec の front matter**: `laws:` / `laws-status: drafted` は提案に留め、適用は人が行う（PRD DC_002）。
6. **bend 不在**: 生成・静的チェックは動く。検査は run-checklist に委ね TOOL_NOT_FOUND になる。スキルは `bend` を呼ばない。

7. **ゲートでの warning（FR-013）**: 節ハッシュのずれは `CHK-205` に warning として併記する。承認も PASS も変えない。
8. **既存 `LAWS.bend` がある場合**: 既定は温存し、再生成案は `LAWS.draft.bend` に出す。承認行ありは上書き不可。
9. **第 1 弾 spec の最小修正**: `drafted` の主体の文言のみ「提案／人が適用」に揃えた（ADR に例外として記録）。

## 実装チケットへの分割案

| # | 内容 |
|:--|:--|
| 1 | スクリプト: 節ハッシュ・静的チェック・承認有効性判定（`laws_header.py` 再利用）とユニットテスト |
| 2 | スキル `draft-laws`（SKILL.md、テンプレート en/ja、`laws.max_laws` の config 読み込み） |
| 3 | post-tool-use: `laws:` を持つ spec 編集時の促し（FR-011） |
| 4 | README / CHANGELOG の追従（利用者向け説明）、stale-doc-detection_spec / front-matter-validation_spec の追従 |
| 6 | run-verification.py の proof に節ハッシュのずれの warning を併記（FR-013）。共有モジュールの節ハッシュをフックと共用 |
| 5 | 検収: proof-gate の spec から 5 法則を再現（`.sdd/laws/` の既存ファイルは変更しない） |

## 他 spec への適用（別チケット提案）

proof-gate 以外の spec への適用は、本設計の対象に含めない。実装後に、判定表を持つ spec（例: run-checklist）から試す別チケットを提案する。

## PRD 変更提案（人の判断。本 PR では変更しない）

PRD FR_006 に次を提案する: (1) 承認の有効性（内容ハッシュ一致）がモデル・証明の作成の前提である旨、(2) 検証方法への静的チェックの追加、(3) 抽出元を「制約事項・機能要件表」から「判定表・集約規則・制約事項など構造化された節（FR 表の散文のみは対象外）」へ改める。
