"""doc_walker.py のユニットテスト（pytest）。

対象選択ルール（requirement=全.md / specification=_spec・_design / task=全.md）と
design doc 探索を検証する。
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
    def test_requirement_all_specification_filtered(self, tmp_path):
        _seed(tmp_path)
        targets = dw.iter_target_files(str(tmp_path), ".sdd", "requirement", "specification")
        names = sorted(Path(p).name for p in targets)
        # requirement: index.md, child.md; specification: only _spec/_design (not notes.md); no task
        assert names == ["a_design.md", "a_spec.md", "child.md", "index.md"]

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
        assert names == ["a_design.md", "a_spec.md", "child.md", "index.md", "log.md"]

    def test_specification_excludes_plain_md(self, tmp_path):
        _seed(tmp_path)
        docs = dw.collect_documents(tmp_path / ".sdd", "requirement", "specification", "task")
        assert "notes.md" not in [p.name for p in docs]


class TestFindDesignDoc:
    def test_finds_recursively(self, tmp_path):
        spec = tmp_path / "spec" / "auth"
        spec.mkdir(parents=True)
        target = spec / "user-login_design.md"
        target.write_text("# d", encoding="utf-8")
        assert dw.find_design_doc(str(tmp_path / "spec"), "user-login") == str(target)

    def test_returns_empty_when_absent(self, tmp_path):
        (tmp_path / "spec").mkdir()
        assert dw.find_design_doc(str(tmp_path / "spec"), "missing") == ""
