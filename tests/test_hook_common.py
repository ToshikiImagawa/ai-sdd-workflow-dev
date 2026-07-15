"""hook_common.py のユニットテスト（pytest）。

stdin JSON 解析、プロジェクトルート解決、.sdd-config.json 読み込み、
フック出力エミッション、相対パス計算を検証する。リファクタ前の安全網。
"""

import importlib.util
import io
import json
import os
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "hook_common.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("hook_common", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hc = _load_module()


# --- read_stdin_json -------------------------------------------------------


class TestReadStdinJson:
    def test_valid_dict(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO('{"a": 1}'))
        assert hc.read_stdin_json() == {"a": 1}

    def test_invalid_json_returns_empty(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
        assert hc.read_stdin_json() == {}

    def test_non_dict_returns_empty(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO("[1, 2, 3]"))
        assert hc.read_stdin_json() == {}


# --- get_project_root ------------------------------------------------------


class TestGetProjectRoot:
    def test_uses_payload_cwd_when_valid_dir(self, tmp_path):
        assert hc.get_project_root({"cwd": str(tmp_path)}) == str(tmp_path)

    def test_falls_back_to_env_when_cwd_invalid(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        assert hc.get_project_root({"cwd": "/no/such/dir"}) == str(tmp_path)

    def test_falls_back_to_getcwd(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
        monkeypatch.chdir(tmp_path)
        assert hc.get_project_root({}) == os.getcwd()


# --- load_sdd_paths --------------------------------------------------------


class TestLoadSddPaths:
    def test_defaults_when_config_missing(self, tmp_path):
        assert hc.load_sdd_paths(str(tmp_path)) == (
            ".sdd", "requirement", "specification",
        )

    def test_reads_custom_paths(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text(
            json.dumps({
                "root": "docs",
                "directories": {"requirement": "reqs", "specification": "specs"},
            }),
            encoding="utf-8",
        )
        assert hc.load_sdd_paths(str(tmp_path)) == ("docs", "reqs", "specs")

    def test_broken_config_falls_back_to_defaults(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text("{ broken", encoding="utf-8")
        assert hc.load_sdd_paths(str(tmp_path)) == (
            ".sdd", "requirement", "specification",
        )

    def test_partial_config_merges_defaults(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text(
            json.dumps({"root": "docs"}), encoding="utf-8",
        )
        assert hc.load_sdd_paths(str(tmp_path)) == (
            "docs", "requirement", "specification",
        )


# --- relative_to_project ---------------------------------------------------


class TestRelativeToProject:
    def test_inside_project(self, tmp_path):
        target = tmp_path / "sub" / "file.md"
        assert hc.relative_to_project(str(target), str(tmp_path)) == os.path.join(
            "sub", "file.md"
        )

    def test_outside_project_returns_empty(self, tmp_path):
        outside = tmp_path.parent / "other" / "file.md"
        assert hc.relative_to_project(str(outside), str(tmp_path / "proj")) == ""


# --- emit_* ----------------------------------------------------------------


class TestEmit:
    def test_emit_permission_deny_shape(self, capsys):
        hc.emit_permission_deny("PreToolUse", "nope")
        out = json.loads(capsys.readouterr().out)
        hso = out["hookSpecificOutput"]
        assert hso["hookEventName"] == "PreToolUse"
        assert hso["permissionDecision"] == "deny"
        assert hso["permissionDecisionReason"] == "nope"

    def test_emit_additional_context_shape(self, capsys):
        hc.emit_additional_context("PostToolUse", "ctx")
        out = json.loads(capsys.readouterr().out)
        hso = out["hookSpecificOutput"]
        assert hso["hookEventName"] == "PostToolUse"
        assert hso["additionalContext"] == "ctx"

    def test_emit_preserves_non_ascii(self, capsys):
        hc.emit_additional_context("PostToolUse", "日本語")
        assert "日本語" in capsys.readouterr().out


class TestSourceExtensions:
    def test_common_extensions_present(self):
        for ext in (".py", ".ts", ".go", ".rs", ".java"):
            assert ext in hc.SOURCE_EXTENSIONS
