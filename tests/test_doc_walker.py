"""doc_walker.py のユニットテスト（pytest）。

対象選択ルール（requirement=全.md / specification=全.md（サフィックス任意） / task=全.md）と
spec 探索を検証する。
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "doc_walker.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("doc_walker", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dw = _load_module()


def _seed(base: Path):
    (base / ".sdd" / "requirement" / "nested").mkdir(parents=True)
    (base / ".sdd" / "specification").mkdir(parents=True)
    (base / ".sdd" / "task").mkdir(parents=True)
    (base / ".sdd" / "requirement" / "index.md").write_text("# i", encoding="utf-8")
    (base / ".sdd" / "requirement" / "nested" / "child.md").write_text("# c", encoding="utf-8")
    (base / ".sdd" / "specification" / "a_spec.md").write_text("# s", encoding="utf-8")
    (base / ".sdd" / "specification" / "a_design.md").write_text("# d", encoding="utf-8")
    (base / ".sdd" / "specification" / "notes.md").write_text("# n", encoding="utf-8")
    (base / ".sdd" / "task" / "log.md").write_text("# l", encoding="utf-8")


class TestIterTargetFiles:
    def test_requirement_and_specification_all_md(self, tmp_path):
        _seed(tmp_path)
        targets = dw.iter_target_files(str(tmp_path), ".sdd", "requirement", "specification")
        names = sorted(Path(p).name for p in targets)
        # requirement: index.md, child.md; specification: every .md, suffix optional; no task
        assert names == ["a_design.md", "a_spec.md", "child.md", "index.md", "notes.md"]

    def test_globally_sorted_strings(self, tmp_path):
        _seed(tmp_path)
        targets = dw.iter_target_files(str(tmp_path), ".sdd", "requirement", "specification")
        assert targets == sorted(targets)

    def test_missing_dirs_returns_empty(self, tmp_path):
        assert dw.iter_target_files(str(tmp_path), ".sdd", "requirement", "specification") == []


class TestCollectDocuments:
    def test_includes_task_and_section_order(self, tmp_path):
        _seed(tmp_path)
        docs = dw.collect_documents(tmp_path / ".sdd", "requirement", "specification", "task")
        names = sorted(p.name for p in docs)
        assert names == ["a_design.md", "a_spec.md", "child.md", "index.md", "log.md", "notes.md"]

    def test_specification_includes_plain_md(self, tmp_path):
        # Suffix is optional under specification/ (issue #84).
        _seed(tmp_path)
        docs = dw.collect_documents(tmp_path / ".sdd", "requirement", "specification", "task")
        assert "notes.md" in [p.name for p in docs]


class TestFindSpecDoc:
    def test_finds_suffixed_spec_recursively(self, tmp_path):
        spec = tmp_path / "spec" / "auth"
        spec.mkdir(parents=True)
        target = spec / "user-login_spec.md"
        target.write_text("# s", encoding="utf-8")
        assert dw.find_spec_doc(str(tmp_path / "spec"), "user-login") == str(target)

    def test_finds_suffixless_spec(self, tmp_path):
        # The _spec suffix is optional under specification/ (issue #84).
        spec = tmp_path / "spec" / "auth"
        spec.mkdir(parents=True)
        target = spec / "user-login.md"
        target.write_text("# s", encoding="utf-8")
        assert dw.find_spec_doc(str(tmp_path / "spec"), "user-login") == str(target)

    def test_suffixed_spec_wins_over_suffixless(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        (spec / "user-login.md").write_text("# plain", encoding="utf-8")
        suffixed = spec / "user-login_spec.md"
        suffixed.write_text("# s", encoding="utf-8")
        assert dw.find_spec_doc(str(spec), "user-login") == str(suffixed)

    def test_design_doc_never_matches(self, tmp_path):
        # design docs are no longer a valid sync target (v5.0.0).
        spec = tmp_path / "spec"
        spec.mkdir()
        (spec / "user-login_design.md").write_text("# d", encoding="utf-8")
        assert dw.find_spec_doc(str(spec), "user-login") == ""

    def test_deterministic_when_stem_collides(self, tmp_path):
        spec = tmp_path / "spec"
        (spec / "b").mkdir(parents=True)
        (spec / "a").mkdir()
        (spec / "b" / "dup_spec.md").write_text("# b", encoding="utf-8")
        (spec / "a" / "dup_spec.md").write_text("# a", encoding="utf-8")
        assert dw.find_spec_doc(str(spec), "dup") == str(spec / "a" / "dup_spec.md")

    def test_returns_empty_when_absent(self, tmp_path):
        (tmp_path / "spec").mkdir()
        assert dw.find_spec_doc(str(tmp_path / "spec"), "missing") == ""
