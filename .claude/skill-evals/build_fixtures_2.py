#!/usr/bin/env python3
"""残り9スキル用の世代別フィクスチャ（build_fixtures.py の続き）。

build_fixtures.py と同じ .sdd/ 世界（notification-badge 機能）を共有しつつ、
6 スキル（checklist / clarify / run-checklist / recommend-front-matter /
constitution / sdd-init）分の追加フィクスチャを組み立てる。

vibe-detector / generate-requirements-diagram / generate-usecase-diagram は
プロンプトのテキストだけで完結するスキルなので、ディレクトリフィクスチャを
必要としない（.sdd/ を読まない）。これらは実行時に `.sdd/CONSTITUTION.md`
だけ置いた最小フィクスチャで十分。

使い方:
    python3 .claude/skill-evals/build_fixtures_2.py <出力ディレクトリ>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_fixtures import (  # noqa: E402
    DESIGN_BODY,
    IMPL_INCOMPLETE,
    PRD_BODY_FULL,
    SPEC_BODY,
    TASKS_ROWS,
    TESTS_COMPLETE,
    fm,
    old_constitution,
)

# --- run-checklist 用: checklist.md 本文 -----------------------------------
# CHK-101 は既に手動チェック済み（上書きされてはいけない）。
# CHK-501 は自動検証可能（pytest）。CHK-701 は自動検証不可（手動確認）。
CHECKLIST_BODY = """# 通知バッジ機能 品質チェックリスト

## Requirements (1xx)

- [x] CHK-101 [P2] PRDの全UR/FRがこのチェックリストでカバーされている（手動確認済み: 2026-09-01）

## Testing (5xx)

- [ ] CHK-501 [P1] ユニットテストが全てpassする

  ```bash
  pytest tests/ -v
  ```

## Security (7xx)

- [ ] CHK-701 [P1] 未読数カウンタに認可チェックがある（他ユーザーのバッジを読めない設計になっているか、コードレビューで確認）
"""


def no_fm_head(id_: str, title: str) -> str:
    """front matter を付けない場合の見出しだけ（recommend-front-matter用）。"""
    return f"# {title}\n\n<!-- id候補: {id_} -->\n\n"


def build_checklist_like(era: str, dest: Path, constitutions: dict[str, str],
                          *, with_checklist: bool, impl_kind: str | None,
                          tests: bool) -> None:
    """checklist / clarify / run-checklist が共有する土台（PRD+spec+design+tasks）。"""
    sdd = dest / ".sdd"
    (sdd / "requirement").mkdir(parents=True, exist_ok=True)
    (sdd / "CONSTITUTION.md").write_text(constitutions[era], encoding="utf-8")

    (sdd / "requirement" / "notification.md").write_text(
        fm(era, id='"prd-notification"', title='"通知機能"', type='"prd"',
           status='"approved"', created='"2026-08-01"', updated='"2026-09-01"',
           depends_on="[]", tags='["notification"]', category='"notification"',
           priority='"medium"', risk='"medium"') + PRD_BODY_FULL,
        encoding="utf-8")

    spec_dir = sdd / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    name = "notification-badge_spec.md" if era == "old" else "notification-badge.md"
    (spec_dir / name).write_text(
        fm(era, id='"spec-notification-badge"', title='"通知バッジ機能"',
           type='"spec"', status='"approved"', sdd_phase='"specify"',
           created='"2026-08-01"', updated='"2026-09-01"',
           depends_on='["prd-notification"]', priority='"medium"', risk='"low"') + SPEC_BODY,
        encoding="utf-8")

    if era == "old":
        design_target = spec_dir / "notification-badge_design.md"
        design_id = '"design-notification-badge"'
    else:
        task_dir = sdd / "task" / "101"
        task_dir.mkdir(parents=True, exist_ok=True)
        design_target = task_dir / "design-draft.md"
        design_id = '"design-101"'
    design_target.write_text(
        fm(era, id=design_id, title='"通知バッジ機能"', type='"design"',
           status='"approved"', sdd_phase='"plan"', impl_status='"in-progress"',
           created='"2026-09-01"', updated='"2026-09-01"',
           depends_on='["spec-notification-badge"]', priority='"medium"',
           risk='"low"') + DESIGN_BODY,
        encoding="utf-8")

    task_dir = sdd / "task" / "101"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "tasks.md").write_text(
        fm(era, id='"task-notification-badge"', title='"通知バッジ機能"', type='"task"',
           status='"in-progress"', sdd_phase='"tasks"',
           created='"2026-09-01"', updated='"2026-09-01"',
           depends_on=f'["{design_id.strip(chr(34))}"]',
           ticket='"101"', priority='"medium"') + "# 通知バッジ機能 タスク分解\n\n## タスク一覧\n\n"
        + TASKS_ROWS.replace("{s}", "done").replace("{s}", "done"),
        encoding="utf-8")

    if with_checklist:
        (task_dir / "checklist.md").write_text(CHECKLIST_BODY, encoding="utf-8")

    if impl_kind:
        src = dest / "src"
        src.mkdir(parents=True, exist_ok=True)
        (src / "__init__.py").write_text("", encoding="utf-8")
        (src / "notification_badge.py").write_text(IMPL_INCOMPLETE, encoding="utf-8")

    if tests:
        t = dest / "tests"
        t.mkdir(parents=True, exist_ok=True)
        (t / "__init__.py").write_text("", encoding="utf-8")
        (t / "test_notification_badge.py").write_text(TESTS_COMPLETE, encoding="utf-8")


def build_recommend_front_matter(era: str, dest: Path, constitutions: dict[str, str]) -> None:
    """front matter を欠いた文書一式（era により対象種別が変わる: new は adr も含む）。"""
    sdd = dest / ".sdd"
    (sdd / "requirement").mkdir(parents=True, exist_ok=True)
    (sdd / "CONSTITUTION.md").write_text(constitutions[era], encoding="utf-8")

    (sdd / "requirement" / "notification.md").write_text(
        no_fm_head("prd-notification", "通知機能 要求仕様書") + PRD_BODY_FULL, encoding="utf-8")

    spec_dir = sdd / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    name = "notification-badge_spec.md" if era == "old" else "notification-badge.md"
    (spec_dir / name).write_text(
        no_fm_head("spec-notification-badge", "通知バッジ機能 抽象仕様書") + SPEC_BODY, encoding="utf-8")

    if era == "old":
        (spec_dir / "notification-badge_design.md").write_text(
            no_fm_head("design-notification-badge", "通知バッジ機能 技術設計") + DESIGN_BODY,
            encoding="utf-8")
    else:
        task_dir = sdd / "task" / "101"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "design-draft.md").write_text(
            no_fm_head("design-101", "通知バッジ機能 技術設計") + DESIGN_BODY, encoding="utf-8")
        adr_dir = sdd / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "notification-badge.md").write_text(
            no_fm_head("adr-notification-badge", "通知バッジ機能 決定ログ")
            + "## 2026-09-01: 未読数はモジュールレベル辞書で保持する\n\n"
              "**理由**: MVPの範囲では永続化要件がない。\n",
            encoding="utf-8")


def build_constitution(era: str, dest: Path, constitutions: dict[str, str]) -> None:
    """constitution スキル用: 原則ドキュメント + それを検証する対象spec。"""
    sdd = dest / ".sdd"
    sdd.mkdir(parents=True, exist_ok=True)
    (sdd / "CONSTITUTION.md").write_text(constitutions[era], encoding="utf-8")
    spec_dir = sdd / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    name = "notification-badge_spec.md" if era == "old" else "notification-badge.md"
    (spec_dir / name).write_text(
        fm(era, id='"spec-notification-badge"', title='"通知バッジ機能"',
           type='"spec"', status='"approved"', sdd_phase='"specify"',
           created='"2026-08-01"', updated='"2026-09-01"',
           depends_on='["prd-notification"]', priority='"medium"', risk='"low"') + SPEC_BODY,
        encoding="utf-8")


def build_sdd_init(dest: Path) -> None:
    """sdd-init 用: .sdd/ が存在しないまっさらなプロジェクト。"""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "CLAUDE.md").write_text(
        "# プロジェクト設定\n\n"
        "## コーディングスタイル\n\n"
        "- 既存のコードスタイルに従う\n",
        encoding="utf-8")
    (dest / "README.md").write_text("# サンプルプロジェクト\n", encoding="utf-8")


def build_prompt_only(era: str, dest: Path, constitutions: dict[str, str]) -> None:
    """vibe-detector / diagram 系: プロンプトのテキストだけで完結するが、
    .sdd/CONSTITUTION.md の有無で判断が変わらないことを確認するため最小限置く。"""
    sdd = dest / ".sdd"
    sdd.mkdir(parents=True, exist_ok=True)
    (sdd / "CONSTITUTION.md").write_text(constitutions[era], encoding="utf-8")


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
        for skill, impl_kind, tests, with_checklist in (
            ("checklist", None, False, False),
            ("clarify", None, False, False),
            ("run-checklist", "incomplete", True, True),
        ):
            dest = out / era / skill
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)
            build_checklist_like(era, dest, constitutions, with_checklist=with_checklist,
                                  impl_kind=impl_kind, tests=tests)
            print(f"built {era}/{skill}")

        dest = out / era / "recommend-front-matter"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        build_recommend_front_matter(era, dest, constitutions)
        print(f"built {era}/recommend-front-matter")

        dest = out / era / "constitution"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        build_constitution(era, dest, constitutions)
        print(f"built {era}/constitution")

        for skill in ("vibe-detector", "generate-requirements-diagram", "generate-usecase-diagram"):
            dest = out / era / skill
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)
            build_prompt_only(era, dest, constitutions)
            print(f"built {era}/{skill}")

    # sdd-init は era 概念なし（まっさらなプロジェクトは1つだけ）。old/new 両方に同じものを置き、
    # 「どの era のスキル本文を使うか」だけで結果を変える。
    for era in ("old", "new"):
        dest = out / era / "sdd-init"
        if dest.exists():
            shutil.rmtree(dest)
        build_sdd_init(dest)
        print(f"built {era}/sdd-init")

    return 0


if __name__ == "__main__":
    sys.exit(main())
