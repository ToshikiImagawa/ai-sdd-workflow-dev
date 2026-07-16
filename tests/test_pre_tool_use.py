"""pre-tool-use.py のユニットテスト（pytest）。

命名規則検証、セッション marker のサニタイズ、CONSTITUTION の切り詰め、
一度きり注入（marker 存在時 no-op）を検証する。リファクタ前の安全網。
"""

import importlib.util
import os
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "pre-tool-use.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("pre_tool_use", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ptu = _load_module()

REQ = os.path.join(".sdd", "requirement")
SPEC = os.path.join(".sdd", "specification")


# --- validate_naming -------------------------------------------------------


class TestValidateNaming:
    def test_requirement_plain_ok(self):
        rel = os.path.join(REQ, "user-login.md")
        assert ptu.validate_naming(rel, REQ, SPEC) == ""

    def test_requirement_with_spec_suffix_violates(self):
        rel = os.path.join(REQ, "user-login_spec.md")
        assert "Naming violation" in ptu.validate_naming(rel, REQ, SPEC)

    def test_requirement_with_design_suffix_violates(self):
        rel = os.path.join(REQ, "index_design.md")
        assert "Naming violation" in ptu.validate_naming(rel, REQ, SPEC)

    def test_specification_spec_ok(self):
        rel = os.path.join(SPEC, "user-login_spec.md")
        assert ptu.validate_naming(rel, REQ, SPEC) == ""

    def test_specification_design_ok(self):
        rel = os.path.join(SPEC, "index_design.md")
        assert ptu.validate_naming(rel, REQ, SPEC) == ""

    def test_specification_without_suffix_violates(self):
        rel = os.path.join(SPEC, "user-login.md")
        assert "Naming violation" in ptu.validate_naming(rel, REQ, SPEC)

    def test_non_markdown_ignored(self):
        rel = os.path.join(SPEC, "notes.txt")
        assert ptu.validate_naming(rel, REQ, SPEC) == ""

    def test_outside_sdd_dirs_ignored(self):
        assert ptu.validate_naming("src/main.py", REQ, SPEC) == ""


# --- session_marker_path ---------------------------------------------------


class TestSessionMarkerPath:
    def test_sanitizes_unsafe_chars(self):
        path = ptu.session_marker_path("a/b c:d")
        name = os.path.basename(path)
        assert name == "sdd-constitution-injected-a_b_c_d"

    def test_keeps_safe_chars(self):
        path = ptu.session_marker_path("sess-123_ID")
        assert os.path.basename(path) == "sdd-constitution-injected-sess-123_ID"


# --- load_constitution -----------------------------------------------------


class TestLoadConstitution:
    def _write_constitution(self, tmp_path, text):
        sdd = tmp_path / ".sdd"
        sdd.mkdir()
        (sdd / "CONSTITUTION.md").write_text(text, encoding="utf-8")

    def test_missing_returns_empty(self, tmp_path):
        assert ptu.load_constitution(str(tmp_path), ".sdd") == ""

    def test_reads_content(self, tmp_path):
        self._write_constitution(tmp_path, "# Principles")
        assert ptu.load_constitution(str(tmp_path), ".sdd") == "# Principles"

    def test_truncates_long_content(self, tmp_path):
        self._write_constitution(tmp_path, "x" * (ptu.CONSTITUTION_MAX_CHARS + 500))
        result = ptu.load_constitution(str(tmp_path), ".sdd")
        assert result.startswith("x" * 100)
        assert "truncated" in result
        assert len(result) < ptu.CONSTITUTION_MAX_CHARS + 200


# --- maybe_inject_constitution ---------------------------------------------


class TestMaybeInjectConstitution:
    def _setup(self, tmp_path):
        sdd = tmp_path / ".sdd"
        sdd.mkdir()
        (sdd / "CONSTITUTION.md").write_text("# Principles", encoding="utf-8")

    def test_non_source_file_no_output(self, tmp_path, capsys):
        self._setup(tmp_path)
        ptu.maybe_inject_constitution("README.md", str(tmp_path), ".sdd", "s1")
        assert capsys.readouterr().out == ""

    def test_source_file_injects_once(self, tmp_path, capsys, monkeypatch):
        self._setup(tmp_path)
        marker_dir = tmp_path / "markers"
        marker_dir.mkdir()
        monkeypatch.setattr(
            ptu, "session_marker_path",
            lambda sid: str(marker_dir / f"m-{sid}"),
        )
        ptu.maybe_inject_constitution("src/app.py", str(tmp_path), ".sdd", "sess")
        first = capsys.readouterr().out
        assert "Principles" in first
        # 同一セッションの2回目は marker により no-op
        ptu.maybe_inject_constitution("src/app.py", str(tmp_path), ".sdd", "sess")
        assert capsys.readouterr().out == ""

    def test_no_constitution_no_output(self, tmp_path, capsys):
        ptu.maybe_inject_constitution("src/app.py", str(tmp_path), ".sdd", "s1")
        assert capsys.readouterr().out == ""
