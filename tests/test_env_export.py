"""env_export.py のユニットテスト（pytest）。

CLAUDE_ENV_FILE への prefix ベース置換・追記、未設定時の no-op、
他 prefix 行の保持を検証する。
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "env_export.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("env_export", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ee = _load_module()


class TestRewriteExports:
    def test_no_env_file_returns_false(self, monkeypatch):
        monkeypatch.delenv("CLAUDE_ENV_FILE", raising=False)
        assert ee.rewrite_exports("SDD_", ['export SDD_ROOT=".sdd"']) is False

    def test_writes_entries(self, tmp_path, monkeypatch):
        env_file = tmp_path / "env"
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
        assert ee.rewrite_exports("SDD_", ['export SDD_ROOT=".sdd"']) is True
        assert env_file.read_text(encoding="utf-8") == 'export SDD_ROOT=".sdd"\n'

    def test_replaces_stale_prefix_lines(self, tmp_path, monkeypatch):
        env_file = tmp_path / "env"
        env_file.write_text('export SDD_ROOT="old"\n', encoding="utf-8")
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
        ee.rewrite_exports("SDD_", ['export SDD_ROOT="new"'])
        content = env_file.read_text(encoding="utf-8")
        assert content == 'export SDD_ROOT="new"\n'
        assert "old" not in content

    def test_preserves_other_prefix_lines(self, tmp_path, monkeypatch):
        env_file = tmp_path / "env"
        env_file.write_text('export OTHER="keep"\nexport SDD_ROOT="old"\n', encoding="utf-8")
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
        ee.rewrite_exports("SDD_", ['export SDD_ROOT="new"'])
        content = env_file.read_text(encoding="utf-8")
        assert 'export OTHER="keep"' in content
        assert 'export SDD_ROOT="new"' in content
        assert '"old"' not in content

    def test_idempotent_no_duplication(self, tmp_path, monkeypatch):
        env_file = tmp_path / "env"
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
        entries = ['export CHECK_SPEC_CACHE_DIR="/c"', 'export CHECK_SPEC_MAPPING="/m"']
        ee.rewrite_exports("CHECK_SPEC_", entries)
        ee.rewrite_exports("CHECK_SPEC_", entries)
        content = env_file.read_text(encoding="utf-8")
        assert content.count('export CHECK_SPEC_CACHE_DIR="/c"') == 1
