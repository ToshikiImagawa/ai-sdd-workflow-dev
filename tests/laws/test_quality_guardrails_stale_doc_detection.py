"""spec-quality-guardrails-stale-doc-detection の点命題を実装に対して検証する差分テスト。

stale-doc-detection_spec 3.1.1 の判定表（旧 .sdd/laws/quality-guardrails/stale-doc-detection/ の点命題）を
実装 post-tool-use.py に対して assert する（laws-drafting_spec FR-014）。モデル API は category_for_path(path_kind) -> Nat
（path_kind: 0=spec 1=spec+laws 2=PRD 3=adr 4=.bend 5=source+spec 6=source modeled 7=none、
category: 0=FR-001 1=FR-009 2=FR-002 3=FR-006 4=FR-007 5=FR-003 6=FR-008 7=出力なし）。
実装は多重該当で複数メッセージを出す（spec 3.1.1 も「多重該当しうる」）ため、モデルの単一値ではなく
「法則の category のメッセージが含まれる」ことを検証する。post-tool-use.py の private な _MESSAGES に依存する。
"""
# spec: spec-quality-guardrails-stale-doc-detection
# impl-of: plugins/sdd-workflow/scripts/post-tool-use.py

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins" / "sdd-workflow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import hook_common  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


post_tool_use = _load("post_tool_use", SCRIPTS / "post-tool-use.py")

FR_MARK = {
    0: "Verify consistency across PRD <-> spec <-> adr",
    1: "declares laws",
    2: "(PRD) was updated",
    3: "(ADR) was updated",
    4: "--category proof",
    5: "a matching specification",
    6: "is modeled by",
}


@pytest.fixture
def stale_project(tmp_path):
    sdd = tmp_path / ".sdd"
    (sdd / "specification").mkdir(parents=True)
    (sdd / "requirement").mkdir()
    (sdd / "adr").mkdir()
    (sdd / "laws" / "foo").mkdir(parents=True)
    (sdd / "laws" / "m").mkdir(parents=True)
    (sdd / "specification" / "plain_spec.md").write_text("# plain\n", encoding="utf-8")
    (sdd / "specification" / "foo_spec.md").write_text(
        '---\nid: "spec-foo"\ntype: "spec"\nlaws: ["laws/foo"]\n---\n# foo\n', encoding="utf-8")
    (sdd / "laws" / "foo" / "LAWS.bend").write_text("# spec: spec-foo\n\nimport Base\n", encoding="utf-8")
    (sdd / "requirement" / "bar.md").write_text("# bar\n", encoding="utf-8")
    (sdd / "adr" / "baz.md").write_text("# baz\n", encoding="utf-8")
    (sdd / "specification" / "mod_spec.md").write_text("# mod\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "modeled.py").write_text("y = 1\n", encoding="utf-8")
    (sdd / "laws" / "m" / "main.bend").write_text(
        "# spec: spec-m\n# model-of: src/modeled.py\n\nimport Base\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("n\n", encoding="utf-8")
    return tmp_path


def _categories(project, rel_path):
    paths = hook_common.load_sdd_paths(str(project))
    post_tool_use._MESSAGES.clear()
    post_tool_use._process_single_file(rel_path, str(project), paths, flush=False)
    text = "\n".join(t for _, t in post_tool_use._MESSAGES)
    post_tool_use._MESSAGES.clear()
    if not text:
        return {7}
    return {k for k, mark in FR_MARK.items() if mark in text}


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_spec_edit_triggers_fr001(stale_project):
    assert 0 in _categories(stale_project, ".sdd/specification/plain_spec.md")


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_spec_with_laws_triggers_fr009(stale_project):
    assert 1 in _categories(stale_project, ".sdd/specification/foo_spec.md")


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_prd_edit_triggers_fr002(stale_project):
    assert 2 in _categories(stale_project, ".sdd/requirement/bar.md")


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_adr_edit_triggers_fr006(stale_project):
    assert 3 in _categories(stale_project, ".sdd/adr/baz.md")


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_law_file_edit_triggers_fr007(stale_project):
    assert 4 in _categories(stale_project, ".sdd/laws/foo/LAWS.bend")


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_source_with_spec_triggers_fr003(stale_project):
    assert 5 in _categories(stale_project, "src/mod.py")


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_source_modeled_triggers_fr008(stale_project):
    assert 6 in _categories(stale_project, "src/modeled.py")


# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
def test_unrelated_edit_is_silent(stale_project):
    assert _categories(stale_project, "notes.txt") == {7}
