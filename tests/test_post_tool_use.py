"""post-tool-use.py のユニットテスト（pytest）。

spec 探索、ファイルパス抽出、編集後ファイル種別ごとの
リマインダー emit 分岐を検証する。リファクタ前の安全網。
"""

import importlib.util
import os
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "post-tool-use.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("post_tool_use", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ptu = _load_module()

SPEC = os.path.join(".sdd", "specification")
PATHS = ptu.SddPaths()


def _process(rel_path: str, project_root) -> None:
    """Run the per-file hook logic against the default .sdd layout."""
    ptu._process_single_file(rel_path, str(project_root), PATHS)


# --- find_spec_doc ---------------------------------------------------------


class TestFindSpecDoc:
    def test_reexports_the_shared_implementation(self):
        # Behavior is covered by tests/test_doc_walker.py; assert only the wiring
        # so a future local reimplementation is caught here.
        assert ptu.find_spec_doc.__module__ == "doc_walker"


# --- _extract_file_paths ---------------------------------------------------


class TestExtractFilePaths:
    def test_write_single_path(self):
        payload = {"tool_input": {"file_path": "a.py"}}
        assert ptu._extract_file_paths(payload) == ["a.py"]

    def test_multiedit_paths_deduped(self):
        payload = {"tool_input": {"edits": [
            {"file_path": "a.py"}, {"file_path": "b.py"}, {"file_path": "a.py"},
        ]}}
        assert ptu._extract_file_paths(payload) == ["a.py", "b.py"]

    def test_empty_payload(self):
        assert ptu._extract_file_paths({}) == []


# --- _process_single_file --------------------------------------------------


class TestProcessSingleFile:
    def test_specification_md_emits_consistency_reminder(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: None)
        _process(os.path.join(SPEC, "user-login_spec.md"), tmp_path)
        out = capsys.readouterr().out
        assert "PRD <-> spec <-> adr" in out
        assert "/constitution validate" in out

    def test_requirement_md_emits_propagation_reminder(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: None)
        _process(os.path.join(PATHS.requirement_prefix, "user-login.md"), tmp_path)
        out = capsys.readouterr().out
        assert "(PRD) was updated" in out
        assert "/constitution validate" in out

    def test_adr_md_emits_append_only_reminder(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: None)
        _process(os.path.join(PATHS.adr_prefix, "user-login.md"), tmp_path)
        out = capsys.readouterr().out
        assert "(ADR) was updated" in out
        assert "append-only" in out

    def test_adr_md_reindexes(self, tmp_path, monkeypatch):
        # adr/ is now an sdd_index target (issue #92), so editing it must
        # trigger the same reindex as specification/.
        calls = []
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: calls.append(a))
        _process(os.path.join(PATHS.adr_prefix, "user-login.md"), tmp_path)
        assert calls

    def test_other_sdd_file_no_output(self, tmp_path, capsys):
        _process(os.path.join(".sdd", "CONSTITUTION.md"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_task_dir_file_no_output(self, tmp_path, capsys):
        # task/ is temporary; the design draft there is not a sync target.
        _process(
            os.path.join(PATHS.task_prefix, "90", "design-draft.md"), tmp_path,
        )
        assert capsys.readouterr().out == ""

    def test_source_with_matching_spec_emits_sync_reminder(
        self, tmp_path, capsys
    ):
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app_spec.md").write_text("# s", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        out = capsys.readouterr().out
        assert "matching specification" in out
        assert "app_spec.md" in out
        assert "keep it as the source of truth" in out

    def test_source_with_suffixless_spec_emits_sync_reminder(
        self, tmp_path, capsys
    ):
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app.md").write_text("# s", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        assert "matching specification" in capsys.readouterr().out

    def test_source_with_only_design_doc_no_output(self, tmp_path, capsys):
        # A leftover v4.x design doc is not a spec, so it must not trigger the
        # reminder (the design doc is no longer a persistent sync target).
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app_design.md").write_text("# d", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_source_without_spec_no_output(self, tmp_path, capsys):
        (tmp_path / SPEC).mkdir(parents=True)
        _process(os.path.join("src", "app.py"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_non_source_file_no_output(self, tmp_path, capsys):
        (tmp_path / SPEC).mkdir(parents=True)
        _process("notes.txt", tmp_path)
        assert capsys.readouterr().out == ""
