#!/usr/bin/env python3
"""高難度タスク(要求同士が競合する機能)版の世代別フィクスチャ。

build_fixtures.py / build_fixtures_2.py と同じ世代別フィクスチャの枠組みを使うが、
題材を「マルチデバイス通知配信システム」に変更する。この題材は PRD の時点で
FR-101(即時配信)と FR-102(バッチ抑制)が文面上明確に矛盾しており、かつ
design 側がその矛盾を明示的なフラグなしに一方的な判断(先頭3件のみ即時)で
黙って解決してしまっている。単純な機能(notification-badge)では skill 有無の差が
見えにくかったため、「誤ると手戻りが大きい・要求が競合する」複雑さを持つ題材で
再検証する。

使い方:
    python3 .claude/skill-evals/build_fixtures_hard.py <出力ディレクトリ>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_fixtures import fm, old_constitution  # noqa: E402

PRD_BODY = """# マルチデバイス通知配信 要求仕様書

## Overview

複数デバイス(スマートフォン・タブレット・PC)を使うユーザーに対し、新着メッセージの通知を配信する。
ユーザーからは「見逃したくない」と「通知の洪水に悩まされたくない」という、一見相反する要望が
同時に寄せられている。

# 2. Use Case Diagram

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    User((User))
    subgraph System["マルチデバイス通知配信"]
        UC1[即時通知を受け取る]
        UC2[ダイジェスト通知を受け取る]
        UC3[未読バッジを確認する]
    end
    User --> UC1
    User --> UC2
    User --> UC3
```

## Actors

| Actor | Description |
|:---|:---|
| User | 複数デバイスでアプリを使う利用者 |

## Use Cases

| Use Case | Description |
|:---|:---|
| 即時通知を受け取る | 新着メッセージをリアルタイムで通知として受け取る |
| ダイジェスト通知を受け取る | 短時間に大量の通知が発生した場合、まとめて1件の通知として受け取る |
| 未読バッジを確認する | 全デバイスで一致した未読数をバッジとして確認する |

# 3. Requirements Diagram

```mermaid
requirementDiagram

requirement UR_101 {
  id: UR_101
  text: "ユーザーは新着メッセージを見逃したくない"
  risk: high
}

functionalRequirement FR_101 {
  id: FR_101
  text: "システムは新着メッセージ受信後、即座に(目安1秒以内)プッシュ通知を送信する"
  risk: high
}

requirement UR_102 {
  id: UR_102
  text: "ユーザーは短時間に大量の通知が届いて疲弊したくない"
  risk: high
}

functionalRequirement FR_102 {
  id: FR_102
  text: "同一ユーザー宛の通知が5分間に4件以上発生した場合、4件目以降はダイジェスト通知としてまとめて配信する"
  risk: high
}

requirement UR_103 {
  id: UR_103
  text: "ユーザーは複数デバイス間で未読数が食い違わないことを期待する"
  risk: medium
}

functionalRequirement FR_103 {
  id: FR_103
  text: "全デバイスの未読バッジ数は常に一致する"
  risk: medium
}

FR_101 - derives -> UR_101
FR_102 - derives -> UR_102
FR_103 - derives -> UR_103
```

# 4. Detailed Requirements

## 4.1 User Requirements

| ID | Requirement | Priority | Risk |
|:---|:---|:---|:---|
| UR_101 | ユーザーは新着メッセージを見逃したくない | Must | High |
| UR_102 | ユーザーは短時間に大量の通知が届いて疲弊したくない | Must | High |
| UR_103 | ユーザーは複数デバイス間で未読数が食い違わないことを期待する | Should | Medium |

## 4.2 Functional Requirements

| ID | Requirement | Derived From | Priority | Risk | Verification |
|:---|:---|:---|:---|:---|:---|
| FR_101 | システムは新着メッセージ受信後、即座に(目安1秒以内)プッシュ通知を送信する | UR_101 | Must | High | Test |
| FR_102 | 同一ユーザー宛の通知が5分間に4件以上発生した場合、4件目以降はダイジェスト通知としてまとめて配信する | UR_102 | Must | High | Test |
| FR_103 | 全デバイスの未読バッジ数は常に一致する | UR_103 | Should | Medium | Test |

## 4.3 Non-Functional Requirements

| ID | Requirement | Priority | Risk |
|:---|:---|:---|:---|
| NFR_101 | 通知配信の遅延はデバイス間で誤差1秒以内 | Should | Medium |

# 5. Out of Scope

通知の既読管理UI、および過去のダイジェスト履歴の閲覧機能は対象外。
"""

SPEC_BODY = """# マルチデバイス通知配信 抽象仕様書

## 背景

複数デバイスを使うユーザーに新着メッセージを通知する。即時性(FR-101)と通知疲れの抑制(FR-102)
という、要求同士が競合しうる2つの機能要求を同時に満たす必要がある。

## 目的

新着メッセージを可能な限り即座に通知しつつ、短時間に多数発生した場合はダイジェストにまとめる。
また、複数デバイス間でバッジ数の不整合を生じさせない。

## 機能要求

| ID | 内容 | 上流要求 |
|:---|:---|:---|
| FR-101 | `notify(user_id, message)` は新着メッセージ受信後、即座にプッシュ通知を送信する | FR_101 |
| FR-102 | 同一ユーザー宛の通知が5分間に4件以上になった場合、4件目以降はダイジェスト通知としてまとめる | FR_102 |
| FR-103 | `get_unread_badge_count(user_id)` は全デバイスで一致する値を返す | FR_103 |

## Public API

| 関数 | 引数 | 戻り値 | 説明 |
|:---|:---|:---|:---|
| `notify` | `user_id: str, message: str` | `None` | 新着メッセージの通知処理を行う |
| `get_unread_badge_count` | `user_id: str` | `int` | 全デバイス共通の未読バッジ数を返す |

## データモデル

| フィールド | 型 | 説明 |
|:---|:---|:---|
| `notification_log` | `list[dict]` | ユーザーごとの直近5分間の通知送信履歴(タイムスタンプ付き) |

## 制約

- FR-101(即時配信)とFR-102(4件目以降ダイジェスト化)は、同一ユーザーへの5件目以降の通知において
  「即座に送るか」「ダイジェストにまとめるか」が文面上両立しない。この優先順位の決定方法は本仕様書
  では明記していない。
"""

DESIGN_BODY = """# マルチデバイス通知配信 技術設計

## 設計方針

`src/notification_dispatch.py` に以下を実装する:

- `notify(user_id: str, message: str) -> None` — 通知を送信する。内部で直近5分間の送信件数を
  `notification_log` から数え、**3件以下ならその場で即時プッシュ、4件目以降は保留してダイジェストに
  蓄積する**(5分経過後にまとめて1件のダイジェスト通知として送信)。
- `get_unread_badge_count(user_id: str) -> int` — 未読数を返す。即時通知・ダイジェスト通知いずれも
  カウントに加算する。

## アーキテクチャ

サーバー側でユーザーごとの通知カウンタと保留キューをメモリ上で保持する。複数デバイスへの配信は
プッシュ通知サービス経由で行い、バッジ数はサーバー側の値を正とする。

## 技術スタック

- Python 3.11+, pytest
"""

TASKS_ROWS = """### Phase 1: Foundation

| #   | Task            | Description                                  | Completion Criteria          | Dependencies | Status |
|:----|:----------------|:---------------------------------------------|:------------------------------|:-------------|:-------|
| 1.1 | Module skeleton | `src/notification_dispatch.py` を作成       | ファイルが存在しimportできる | -            | {s} |

### Phase 2: Core Implementation

| #   | Task            | Description                                       | Completion Criteria                          | Dependencies | Status |
|:----|:----------------|:---------------------------------------------------|:-----------------------------------------------|:-------------|:-------|
| 2.1 | notify (即時)  | 直近5分3件以内なら即時送信する分岐を実装(FR-101)  | 3件以内は即時送信されるテストが通る            | 1.1          | {s} |
| 2.2 | notify (抑制)  | 4件目以降をダイジェストに蓄積する分岐を実装(FR-102) | 4件目以降がダイジェストに蓄積されるテストが通る | 2.1          | {s} |
| 2.3 | get_unread_badge_count | 全デバイス共通の未読数を返す(FR-103)         | 即時・ダイジェスト双方を含む数が返るテストが通る | 2.2          | {s} |

### Phase 3: Testing

| #   | Task       | Description                                     | Completion Criteria | Dependencies | Status |
|:----|:-----------|:--------------------------------------------------|:---------------------|:-------------|:-------|
| 3.1 | Unit tests | `tests/test_notification_dispatch.py` を作成    | pytest が全て pass  | 2.3          | {s} |
"""


def build(era: str, dest: Path, constitution_text: str) -> None:
    sdd = dest / ".sdd"
    (sdd / "requirement").mkdir(parents=True, exist_ok=True)
    (sdd / "CONSTITUTION.md").write_text(constitution_text, encoding="utf-8")

    (sdd / "requirement" / "notification-dispatch.md").write_text(
        fm(era, id='"prd-notification-dispatch"', title='"マルチデバイス通知配信"', type='"prd"',
           status='"approved"', created='"2026-08-01"', updated='"2026-09-01"',
           depends_on="[]", tags='["notification"]', category='"notification"',
           priority='"high"', risk='"high"') + PRD_BODY,
        encoding="utf-8")

    spec_dir = sdd / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_name = "notification-dispatch_spec.md" if era == "old" else "notification-dispatch.md"
    (spec_dir / spec_name).write_text(
        fm(era, id='"spec-notification-dispatch"', title='"マルチデバイス通知配信"',
           type='"spec"', status='"approved"', sdd_phase='"specify"',
           created='"2026-08-01"', updated='"2026-09-01"',
           depends_on='["prd-notification-dispatch"]', priority='"high"', risk='"high"') + SPEC_BODY,
        encoding="utf-8")

    if era == "old":
        design_target = spec_dir / "notification-dispatch_design.md"
        design_id = '"design-notification-dispatch"'
    else:
        task_dir = sdd / "task" / "201"
        task_dir.mkdir(parents=True, exist_ok=True)
        design_target = task_dir / "design-draft.md"
        design_id = '"design-201"'
    design_target.write_text(
        fm(era, id=design_id, title='"マルチデバイス通知配信"', type='"design"',
           status='"approved"', sdd_phase='"plan"', impl_status='"in-progress"',
           created='"2026-09-01"', updated='"2026-09-01"',
           depends_on='["spec-notification-dispatch"]', priority='"high"',
           risk='"high"') + DESIGN_BODY,
        encoding="utf-8")

    task_dir = sdd / "task" / "201"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "tasks.md").write_text(
        fm(era, id='"task-notification-dispatch"', title='"マルチデバイス通知配信"', type='"task"',
           status='"in-progress"', sdd_phase='"tasks"',
           created='"2026-09-01"', updated='"2026-09-01"',
           depends_on=f'["{design_id.strip(chr(34))}"]',
           ticket='"201"', priority='"high"') + "# マルチデバイス通知配信 タスク分解\n\n## タスク一覧\n\n"
        + TASKS_ROWS.replace("{s}", "in-progress"),
        encoding="utf-8")


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
        dest = out / era / "notification-dispatch"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        build(era, dest, constitutions[era])
        print(f"built {era}/notification-dispatch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
