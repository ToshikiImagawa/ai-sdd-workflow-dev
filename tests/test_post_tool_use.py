"""post-tool-use.py のユニットテスト（pytest）。

design doc 探索、ファイルパス抽出、編集後ファイル種別ごとの
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

REQ = os.path.join(".sdd", "requirement")
SPEC = os.path.join(".sdd", "specification")


# --- find_design_doc -------------------------------------------------------


class TestFindDesignDoc:
    def test_finds_matching_design_doc(self, tmp_path):
        spec_dir = tmp_path / "spec"
        (spec_dir / "auth").mkdir(parents=True)
        target = spec_dir / "auth" / "user-login_design.md"
        target.write_text("# design", encoding="utf-8")
        found = ptu.find_design_doc(str(spec_dir), "user-login")
        assert found == str(target)

    def test_returns_empty_when_absent(self, tmp_path):
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        assert ptu.find_design_doc(str(spec_dir), "missing") == ""


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
        rel = os.path.join(SPEC, "user-login_spec.md")
        ptu._process_single_file(rel, str(tmp_path), ".sdd", REQ, SPEC)
        out = capsys.readouterr().out
        assert "PRD <-> *_spec.md <-> *_design.md" in out

    def test_requirement_md_emits_propagation_reminder(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: None)
        rel = os.path.join(REQ, "user-login.md")
        ptu._process_single_file(rel, str(tmp_path), ".sdd", REQ, SPEC)
        out = capsys.readouterr().out
        assert "(PRD) was updated" in out

    def test_other_sdd_file_no_output(self, tmp_path, capsys):
        rel = os.path.join(".sdd", "CONSTITUTION.md")
        ptu._process_single_file(rel, str(tmp_path), ".sdd", REQ, SPEC)
        assert capsys.readouterr().out == ""

    def test_source_with_matching_design_emits_sync_reminder(
        self, tmp_path, capsys
    ):
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app_design.md").write_text("# d", encoding="utf-8")
        ptu._process_single_file(
            os.path.join("src", "app.py"), str(tmp_path), ".sdd", REQ, SPEC,
        )
        out = capsys.readouterr().out
        assert "keep it as the source of truth" in out

    def test_source_without_design_no_output(self, tmp_path, capsys):
        (tmp_path / SPEC).mkdir(parents=True)
        ptu._process_single_file(
            os.path.join("src", "app.py"), str(tmp_path), ".sdd", REQ, SPEC,
        )
        assert capsys.readouterr().out == ""

    def test_non_source_file_no_output(self, tmp_path, capsys):
        (tmp_path / SPEC).mkdir(parents=True)
        ptu._process_single_file(
            "notes.txt", str(tmp_path), ".sdd", REQ, SPEC,
        )
        assert capsys.readouterr().out == ""
