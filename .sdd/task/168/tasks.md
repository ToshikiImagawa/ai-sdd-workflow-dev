---
id: "task-168"
title: "法則案の生成と承認フロー タスク"
type: "task"
status: "draft"
sdd-phase: "tasks"
created: "2026-10-19"
updated: "2026-10-19"
sdd-version: "5.1.0"
depends-on: ["design-168"]
ticket: "168"
tags: ["laws", "bend", "drafting"]
category: "task-implementation"
---

# タスク（issue #168）

**関連設計:** [design-draft.md](design-draft.md)

## 実装 A（issue #170）: 共有モジュール

| ID | タスク | 対応 FR | 状態 |
|:--|:--|:--|:--|
| A-1 | `laws_header.py` に per-file の import 検査 `file_disallowed_imports` を追加（`disallowed_imports` は挙動不変） | FR-006 #5 | 完了 |
| A-2 | 節の切り出しと節ハッシュ（`find_section` / `section_hash`）。見出しレベル・フェンス・front matter・正規化をテストで固定 | FR-003 | 完了 |
| A-3 | `# source:` / `# model-api:` / `law` 宣言の解析（`parse_source` / `parse_laws` / `model_api_functions`） | FR-003, FR-008 | 完了 |
| A-4 | 静的チェック `static_check`（出典の実在・欠落・重複・自明・import・model-api 整合） | FR-006 | 完了 |
| A-5 | 出典ずれ判定 `source_drift`（ゲートの `warnings` とフックで共用） | FR-011, FR-013 | 完了 |
| A-6 | 承認有効性判定 `approval_status`（`laws_header` を再利用） | FR-007 | 完了 |
| A-7 | ユニットテスト `tests/test_laws_drafting.py`、CHANGELOG（en/ja） | NFR-002 | 完了 |

## 実装 B-1（issue #171）: スキル `draft-laws`

| ID | タスク | 対応 FR | 状態 |
|:--|:--|:--|:--|
| B1-1 | `skills/draft-laws/scripts/draft_laws.py`（status / hash / rank / check / compare。`laws.max_laws` 読み込み、候補の決定的な整列と打ち切り） | FR-004, FR-006, FR-007, NFR-005 | 完了 |
| B1-2 | `SKILL.md`（draft / model）と templates/{en,ja}（法則案・main/PROOF 雛形・抽出レポート） | FR-001〜003, FR-005, FR-007〜010, FR-012 | 完了 |
| B1-3 | 検収（§11）: 独立再現（別セッション。再現元 HEAD d1ce670、§3.1.1 sha256:fa3ebed3050e、内容ハッシュ 2843fb9c5644）で 7 法則を生成。第 1 弾 5 件との対応: 一致 2（`agg_single_identity`=`aggregate_singleton`、`unapproved_never_pass`。後者は spec §4.1 に例があり独立性は弱い）、形違い 1（`agg_pair_commutes` ≒ `worse_commutative`）、2 法則の合算で同範囲 1（`pass_requires_marker` = `approved_exit_failure_fails` + `approved_missing_marker_fails`）、**再現されず 1（`agg_empty_skipped`。spec に空入力の結果の記述が無い）**。片方向の合格条件は未達。対応表を `tests/test_draft_laws_script.py` で固定 | §11 | 実施済み（合格条件は未達。証明段階は bend 無しで未確認） |
| B1-4 | README / CHANGELOG（en/ja） | — | 完了 |

## 実装 B-2（issue #172）: 促しと warning

| ID | タスク | 対応 FR | 状態 |
|:--|:--|:--|:--|
| B2-1 | `post-tool-use.py`: `laws:` を持つ spec の編集時に `source_drift` を使って再抽出を促す（外部 root はスキップ） | FR-011 | 完了 |
| B2-2 | `run-verification.py proof`: 承認有効・孤児でない・`bend` ありの法則ディレクトリに `warnings[]` を加算 | FR-013 | 完了 |
| B2-3 | run-checklist の SKILL.md / テンプレート（en・ja）/ references に `CHK-205` の warning 表示を追記 | FR-013 | 完了 |
| B2-4 | テスト（warning の条件・判定不変・フックの促し）、README / CHANGELOG（en/ja） | NFR-002 | 完了 |

## 後続

- 実装 B-1（#171・上表）: スキル `draft-laws`、`laws.max_laws` の config 読み込み、候補の決定的な整列と上限での打ち切り（NFR-005）
- 実装 B-2（#172）: post-tool-use の促し（FR-011）、`run-verification.py proof` の `warnings`（FR-013）
