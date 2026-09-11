---
id: "task-workflow-foundation-session-config-env-export"
title: "環境変数エクスポートの共通化"
type: "task"
status: "completed"
sdd-phase: "tasks"
ticket: "9004"
created: "2026-09-01"
updated: "2026-09-04"
depends-on: ["design-workflow-foundation-session-config"]
tags: ["session-config", "environment", "refactoring"]
category: "workflow-foundation"
---

# 環境変数エクスポートの共通化 タスクリスト

**対象 Spec:** [session-config_spec.md](../../specification/workflow-foundation/session-config_spec.md)
（FR-003 / NFR-003）
**対象 Design:** [session-config_design.md](../../specification/workflow-foundation/session-config_design.md)

## タスク

| # | タスク                                                          | 完了条件                                                        | 状態 |
|:--|:----------------------------------------------------------------|:----------------------------------------------------------------|:-----|
| 1 | `CLAUDE_ENV_FILE` への書き出しを共通ヘルパーへ切り出す           | 各フックが個別に env ファイルを組み立てていない                   | done |
| 2 | 書き出しを原子的にする（tmp へ書いて replace）                    | 途中状態のファイルを source しうる窓が無い                        | done |
| 3 | 再実行時に同一 prefix の旧 export 行を落とす                      | 同じ prefix で2回書いても重複行が残らない                         | done |
| 4 | 上記3点のユニットテストを追加する                                 | `pytest tests/test_env_export.py` が pass                       | done |
| 5 | `session-start.py` を共通ヘルパー経由へ差し替える                  | ゴールデンファイル回帰が pass                                    | done |

全タスク done。`python3 -m pytest tests/ -v` は全 pass。
