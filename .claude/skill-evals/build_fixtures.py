#!/usr/bin/env python3
"""世代別（v4.x / v5.0.0）の評価用サンドボックスを組み立てる。

`ASSERTION_DESIGN.md` の「世代別フィクスチャ」方針に対応する。各スキルを自分の時代の
レイアウトで評価することで、パス不一致による着手前停止を排除し、方法論そのものの価値を測る。

使い方:
    python3 .claude/skill-evals/build_fixtures.py <出力ディレクトリ>

出力:
    <出力ディレクトリ>/<era>/<skill>/   ... era は "old" | "new"

`CONSTITUTION.md` は世代に一致させる（old は commit ce3fea3 時点のもの）。混ぜると他世代の
規約が漏れ、「スキルの有無」ではなく「フィクスチャに答えが書いてあるか」を測ってしまう。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

OLD_CONSTITUTION_REF = "ce3fea3"

# --- 共通の本文断片 -------------------------------------------------------

PRD_BODY_FULL = """# 通知機能 要求仕様書

## Overview

ユーザーに新着メッセージを知らせる通知機能、および未読メッセージ数のバッジ表示機能。

# 2. Use Case Diagram

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    User((User))
    subgraph System["通知機能"]
        UC1[通知を受け取る]
        UC2[未読バッジを確認する]
    end
    User --> UC1
    User --> UC2
```

## Actors

| Actor | Description |
|:---|:---|
| User | アプリの利用者 |

## Use Cases

| Use Case | Description |
|:---|:---|
| 通知を受け取る | ユーザーが新着メッセージの通知を受け取る |
| 未読バッジを確認する | ユーザーがアプリアイコンの未読バッジで未読数を確認する |

# 3. Requirements Diagram

```mermaid
requirementDiagram

requirement UR_001 {
  id: UR_001
  text: "ユーザーは新着メッセージの通知を受け取りたい"
  risk: medium
}

functionalRequirement FR_001 {
  id: FR_001
  text: "システムは新着メッセージ受信時にプッシュ通知を送信する"
  risk: medium
}

requirement UR_002 {
  id: UR_002
  text: "ユーザーはアプリアイコンで未読メッセージ数を一目で確認したい"
  risk: medium
}

functionalRequirement FR_002 {
  id: FR_002
  text: "システムはアプリアイコンに未読メッセージ数をバッジ表示し、99件を超える場合は99+と表示する"
  risk: medium
}

FR_001 - derives -> UR_001
FR_002 - derives -> UR_002
```

# 4. Detailed Requirements

## 4.1 User Requirements

| ID | Requirement | Priority | Risk |
|:---|:---|:---|:---|
| UR_001 | ユーザーは新着メッセージの通知を受け取りたい | Must | Medium |
| UR_002 | ユーザーはアプリアイコンで未読メッセージ数を一目で確認したい | Must | Medium |

## 4.2 Functional Requirements

| ID | Requirement | Derived From | Priority | Risk | Verification |
|:---|:---|:---|:---|:---|:---|
| FR_001 | システムは新着メッセージ受信時にプッシュ通知を送信する | UR_001 | Must | Medium | Test |
| FR_002 | システムはアプリアイコンに未読メッセージ数をバッジ表示し、99件を超える場合は99+と表示する | UR_002 | Must | Medium | Test |

## 4.3 Non-Functional Requirements

（なし）

# 5. Out of Scope

バッジのクリア操作のUI導線は対象外（APIのみ提供）。
"""

# generate-prd の追記テスト用: UR_002/FR_002 がまだ無い状態
PRD_BODY_PARTIAL = """# 通知機能 要求仕様書

## Overview

ユーザーに新着メッセージを知らせる通知機能。

# 2. Use Case Diagram

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    User((User))
    subgraph System["通知機能"]
        UC1[通知を受け取る]
    end
    User --> UC1
```

## Actors

| Actor | Description |
|:---|:---|
| User | アプリの利用者 |

## Use Cases

| Use Case | Description |
|:---|:---|
| 通知を受け取る | ユーザーが新着メッセージの通知を受け取る |

# 3. Requirements Diagram

```mermaid
requirementDiagram

requirement UR_001 {
  id: UR_001
  text: "ユーザーは新着メッセージの通知を受け取りたい"
  risk: medium
}

functionalRequirement FR_001 {
  id: FR_001
  text: "システムは新着メッセージ受信時にプッシュ通知を送信する"
  risk: medium
}

FR_001 - derives -> UR_001
```

# 4. Detailed Requirements

## 4.1 User Requirements

| ID | Requirement | Priority | Risk |
|:---|:---|:---|:---|
| UR_001 | ユーザーは新着メッセージの通知を受け取りたい | Must | Medium |

## 4.2 Functional Requirements

| ID | Requirement | Derived From | Priority | Risk | Verification |
|:---|:---|:---|:---|:---|:---|
| FR_001 | システムは新着メッセージ受信時にプッシュ通知を送信する | UR_001 | Must | Medium | Test |

## 4.3 Non-Functional Requirements

（なし）

# 5. Out of Scope

未読数のバッジ表示は対象外（本PRDの時点では）。
"""

SPEC_BODY = """# 通知バッジ機能 抽象仕様書

## 背景

ユーザーが未読メッセージ数を一目で確認できるよう、アプリアイコンにバッジ数を表示する。

## 目的

未読メッセージ数をバッジとして正確に表示し、99件を超える場合は "99+" と表示する。
ユーザーはバッジをクリアできる。

## 機能要求

| ID | 内容 | 上流要求 |
|:---|:---|:---|
| FR-001 | `get_unread_badge_count(user_id)` は指定ユーザーの未読メッセージ数を返す | FR_002 |
| FR-002 | 未読数が99を超える場合、数値ではなく文字列 `"99+"` を返す | FR_002 |
| FR-003 | `clear_badge(user_id)` はユーザーのバッジをクリアする(未読数を0扱いにする) | FR_002 |

## Public API

| 関数 | 引数 | 戻り値 | 説明 |
|:---|:---|:---|:---|
| `get_unread_badge_count` | `user_id: str` | `int \\| str` | 未読数、または99超で `"99+"` |
| `clear_badge` | `user_id: str` | `None` | バッジをクリアする |

## データモデル

| フィールド | 型 | 説明 |
|:---|:---|:---|
| `unread_count` | `int` | ユーザーごとの未読メッセージ数 |

## 制約

- 未読数の上限表示は "99+" 固定（100以上はすべて "99+"）
"""

DESIGN_BODY = """# 通知バッジ機能 技術設計

## 設計方針

`src/notification_badge.py` に以下を実装する:

- `increment_unread(user_id: str) -> None` — 未読数を1増やす
- `get_unread_badge_count(user_id: str) -> int | str` — 未読数を返す。99を超える場合は文字列 `"99+"` を返す
- `clear_badge(user_id: str) -> None` — 未読数をクリアする

## アーキテクチャ

モジュールレベルの辞書でユーザーごとの未読数を保持するシンプルな実装とする。
DB永続化は行わない（MVP の範囲では永続化要件がないため）。

## 技術スタック

- Python 3.11+, pytest
"""

# doc-consistency-checker 用: 型注釈が実装と矛盾する記述を意図的に含める（世代非依存の不整合）
DECISION_LOG_BODY = """# 通知バッジ機能 決定ログ

このファイルは append-only の決定ログである。過去のエントリは書き換えず、決定を覆す場合は
新しいエントリを追記する。

---

## 2026-09-01: 未読数の保持をモジュールレベル辞書に決定

**決定**: `_unread_counts: dict[str, user_id, int]` をモジュールレベルの状態として保持し、
DB永続化は行わない。

**理由**: MVPの範囲では永続化要件がなく、シンプルな実装を優先した（FR-001〜FR-003のみが対象）。

**却下した代替案**:

- **DBテーブルでの永続化**: プロセス再起動でバッジがリセットされる問題が出た場合に検討する。
"""

TASKS_ROWS = """### Phase 1: Foundation

| #   | Task            | Description                                  | Completion Criteria          | Dependencies | Status |
|:----|:----------------|:---------------------------------------------|:-----------------------------|:-------------|:-------|
| 1.1 | Module skeleton | `src/notification_badge.py` を作成し内部状態を定義 | ファイルが存在しimportできる | -            | {s} |

### Phase 2: Core Implementation

| #   | Task                   | Description                               | Completion Criteria                        | Dependencies | Status |
|:----|:-----------------------|:------------------------------------------|:-------------------------------------------|:-------------|:-------|
| 2.1 | increment_unread       | 未読数を1増やす関数を実装                 | テストが通る                               | 1.1          | {s} |
| 2.2 | get_unread_badge_count | 未読数を返す。99超で "99+" を返す(FR-002) | 99以下は数値、100以上は "99+" を返すテストが通る | 2.1     | {s} |
| 2.3 | clear_badge            | バッジをクリアする(FR-003)                | クリア後に未読数が0になるテストが通る      | 2.1          | {s} |

### Phase 3: Testing

| #   | Task       | Description                               | Completion Criteria | Dependencies | Status |
|:----|:-----------|:------------------------------------------|:--------------------|:-------------|:-------|
| 3.1 | Unit tests | `tests/test_notification_badge.py` を作成 | pytest が全て pass  | 2.3          | {s} |
"""

IMPL_COMPLETE = '''"""Notification badge feature."""

_unread_counts: dict[str, int] = {}


def increment_unread(user_id: str) -> None:
    _unread_counts[user_id] = _unread_counts.get(user_id, 0) + 1


def get_unread_badge_count(user_id: str) -> int | str:
    count = _unread_counts.get(user_id, 0)
    return "99+" if count > 99 else count


def clear_badge(user_id: str) -> None:
    _unread_counts[user_id] = 0
'''

# check-spec 用: FR-002（99+上限）と FR-003（clear_badge）が未実装
IMPL_INCOMPLETE = '''"""Notification badge feature."""

_unread_counts: dict[str, int] = {}


def increment_unread(user_id: str) -> None:
    _unread_counts[user_id] = _unread_counts.get(user_id, 0) + 1


def get_unread_badge_count(user_id: str) -> int:
    return _unread_counts.get(user_id, 0)
'''

TESTS_COMPLETE = '''from src.notification_badge import clear_badge, get_unread_badge_count, increment_unread


def test_increment_and_get():
    increment_unread("u1")
    increment_unread("u1")
    assert get_unread_badge_count("u1") == 2


def test_99_plus_cap():
    for _ in range(150):
        increment_unread("u2")
    assert get_unread_badge_count("u2") == "99+"


def test_clear_badge():
    increment_unread("u3")
    clear_badge("u3")
    assert get_unread_badge_count("u3") == 0
'''


def fm(era: str, **fields: str) -> str:
    """front matter を組み立てる。sdd-version は new 世代のみ付与する。"""
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key.replace('_', '-')}: {value}")
    if era == "new":
        lines.append('sdd-version: "4.1.0"')
    lines.append("---")
    return "\n".join(lines) + "\n\n"


# --- スキル別のフィクスチャ構成 -------------------------------------------
#
# prd:    "full" | "partial" | None
# spec:   True | False
# design: True | False
# tasks:  "pending" | "done" | None
# decisions: 決定ログを置くか（new 世代は adr/、old 世代は設計書内に追記）
# impl:   "complete" | "incomplete" | None
# tests:  True | False

SKILLS: dict[str, dict] = {
    "generate-spec": dict(prd="full", spec=False, design=False, tasks=None,
                          decisions=False, impl=None, tests=False),
    "check-spec": dict(prd="full", spec=True, design=True, tasks=None,
                       decisions=False, impl="incomplete", tests=False),
    "implement": dict(prd="full", spec=True, design=True, tasks="pending",
                      decisions=False, impl=None, tests=False),
    "generate-prd": dict(prd="partial", spec=False, design=False, tasks=None,
                         decisions=False, impl=None, tests=False),
    "finalize-prd": dict(prd="partial", spec=False, design=False, tasks=None,
                         decisions=False, impl=None, tests=False),
    "analyze-requirements": dict(prd=None, spec=False, design=False, tasks=None,
                                 decisions=False, impl=None, tests=False),
    "task-breakdown": dict(prd="full", spec=True, design=True, tasks=None,
                           decisions=False, impl=None, tests=False),
    "task-cleanup": dict(prd="full", spec=True, design=True, tasks="done",
                         decisions=False, impl="complete", tests=True),
    "plan-refactor": dict(prd="full", spec=True, design=True, tasks=None,
                          decisions=True, impl="complete", tests=True),
    "doc-consistency-checker": dict(prd="full", spec=True, design=True, tasks=None,
                                    decisions=True, impl="complete", tests=True),
}


def old_constitution(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "show", f"{OLD_CONSTITUTION_REF}:.sdd/CONSTITUTION.md"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout


def build(era: str, skill: str, cfg: dict, dest: Path, constitutions: dict[str, str]) -> None:
    sdd = dest / ".sdd"
    (sdd / "requirement").mkdir(parents=True, exist_ok=True)
    (sdd / "CONSTITUTION.md").write_text(constitutions[era], encoding="utf-8")

    if cfg["prd"]:
        body = PRD_BODY_FULL if cfg["prd"] == "full" else PRD_BODY_PARTIAL
        (sdd / "requirement" / "notification.md").write_text(
            fm(era, id='"prd-notification"', title='"通知機能"', type='"prd"',
               status='"approved"', created='"2026-08-01"', updated='"2026-09-01"',
               depends_on="[]", tags='["notification"]', category='"notification"',
               priority='"medium"', risk='"medium"') + body,
            encoding="utf-8")

    if cfg["spec"]:
        spec_dir = sdd / "specification"
        spec_dir.mkdir(parents=True, exist_ok=True)
        # old 世代は _spec サフィックス必須、new 世代はサフィックス任意
        name = "notification-badge_spec.md" if era == "old" else "notification-badge.md"
        impl_status = ('impl-status: "implemented"\n'
                       if (era == "new" and cfg["impl"]) else "")
        head = fm(era, id='"spec-notification-badge"', title='"通知バッジ機能"',
                  type='"spec"', status='"approved"', sdd_phase='"specify"',
                  created='"2026-08-01"', updated='"2026-09-01"',
                  depends_on='["prd-notification"]', priority='"medium"', risk='"low"')
        if impl_status:
            head = head.rstrip("\n")[: -len("---")] + impl_status + "---\n\n"
        (spec_dir / name).write_text(head + SPEC_BODY, encoding="utf-8")

    if cfg["design"]:
        design_body = DESIGN_BODY
        if cfg["decisions"] and era == "old":
            # old 世代は決定ログの置き場が *_design.md 自身
            design_body += "\n## 設計判断の記録\n\n" + DECISION_LOG_BODY.split("---\n", 1)[1]
        if era == "old":
            spec_dir = sdd / "specification"
            spec_dir.mkdir(parents=True, exist_ok=True)
            target = spec_dir / "notification-badge_design.md"
            design_id = '"design-notification-badge"'
        else:
            task_dir = sdd / "task" / "101"
            task_dir.mkdir(parents=True, exist_ok=True)
            target = task_dir / "design-draft.md"
            design_id = '"design-101"'
        target.write_text(
            fm(era, id=design_id, title='"通知バッジ機能"', type='"design"',
               status='"approved"', sdd_phase='"plan"',
               impl_status='"implemented"' if cfg["impl"] == "complete" else '"not-implemented"',
               created='"2026-09-01"', updated='"2026-09-01"',
               depends_on='["spec-notification-badge"]', priority='"medium"',
               risk='"low"') + design_body,
            encoding="utf-8")

    if cfg["decisions"] and era == "new":
        adr_dir = sdd / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "notification-badge.md").write_text(
            fm(era, id='"adr-notification-badge"', title='"通知バッジ機能 決定ログ"',
               type='"adr"', status='"approved"', sdd_phase='"implement"',
               created='"2026-09-01"', updated='"2026-09-01"',
               depends_on='["spec-notification-badge"]', tags='["notification-badge"]',
               category='"notification"') + DECISION_LOG_BODY,
            encoding="utf-8")

    if cfg["tasks"]:
        task_dir = sdd / "task" / "101"
        task_dir.mkdir(parents=True, exist_ok=True)
        done = cfg["tasks"] == "done"
        status = "done" if done else "pending"
        body = ("# 通知バッジ機能 タスク分解\n\n## タスク一覧\n\n"
                + TASKS_ROWS.replace("{s}", status))
        if done:
            body += "\n## 実装完了メモ\n\n全タスク完了。`pytest tests/` は3件すべて pass。\n"
        (task_dir / "tasks.md").write_text(
            fm(era, id='"task-notification-badge"', title='"通知バッジ機能"', type='"task"',
               status='"done"' if done else '"pending"', sdd_phase='"tasks"',
               created='"2026-09-01"', updated='"2026-09-01"',
               depends_on=f'["{"design-notification-badge" if era == "old" else "design-101"}"]',
               ticket='"101"', priority='"medium"') + body,
            encoding="utf-8")

    if cfg["impl"]:
        src = dest / "src"
        src.mkdir(parents=True, exist_ok=True)
        (src / "__init__.py").write_text("", encoding="utf-8")
        (src / "notification_badge.py").write_text(
            IMPL_COMPLETE if cfg["impl"] == "complete" else IMPL_INCOMPLETE,
            encoding="utf-8")

    if cfg["tests"]:
        tests = dest / "tests"
        tests.mkdir(parents=True, exist_ok=True)
        (tests / "__init__.py").write_text("", encoding="utf-8")
        (tests / "test_notification_badge.py").write_text(TESTS_COMPLETE, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    repo_root = Path(__file__).resolve().parents[2]
    constitutions = {
        "old": old_constitution(repo_root),
        "new": (repo_root / ".sdd" / "CONSTITUTION.md").read_text(encoding="utf-8"),
    }
    for era in ("old", "new"):
        for skill, cfg in SKILLS.items():
            dest = out / era / skill
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)
            build(era, skill, cfg, dest, constitutions)
            print(f"built {era}/{skill}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
