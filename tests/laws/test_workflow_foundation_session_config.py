"""spec-workflow-foundation-session-config の点命題を実装に対して検証する差分テスト。

.sdd/laws/workflow-foundation/session-config/LAWS.bend の法則を実装 session-start.py / hook_common.py に対して
assert する（laws-drafting_spec FR-014）。モデル API は normalize_index(value_kind) -> Bool
（0=欠落 1=true 2=false 3=不正値）と resolve_value(has_config, has_env) -> Nat（0=config 1=env 2=default）。
bend は不要。
"""
# spec: spec-workflow-foundation-session-config
# impl-of: plugins/sdd-workflow/scripts/session-start.py
# impl-of: plugins/sdd-workflow/scripts/hook_common.py

import importlib.util
import json
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


session_start = _load("session_start", SCRIPTS / "session-start.py")


# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
def test_index_absent_defaults_true():
    assert session_start.parse_index_flag(None) is True
    assert session_start.build_sdd_config({}, "en").index is True


# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
def test_index_true_preserved():
    assert session_start.build_sdd_config({"index": True}, "en").index is True


# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
def test_index_false_preserved():
    assert session_start.build_sdd_config({"index": False}, "en").index is False


# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
@pytest.mark.parametrize("bad", ["on", "off", 1, 0, "true", [], {}])
def test_index_invalid_defaults_true(bad, capsys):
    assert session_start.build_sdd_config({"index": bad}, "en").index is True


def _resolve(tmp_path, monkeypatch, has_config, has_env):
    if has_config:
        (tmp_path / ".sdd-config.json").write_text(
            json.dumps({"lang": "ja", "root": "docs/sdd"}), encoding="utf-8")
    if has_env:
        monkeypatch.setenv("SDD_LANG", "fr")
        monkeypatch.setenv("SDD_ROOT", "envroot")
    else:
        monkeypatch.delenv("SDD_LANG", raising=False)
        monkeypatch.delenv("SDD_ROOT", raising=False)
    lang, root = hook_common.resolve_lang_and_root(tmp_path)
    return {("ja", "docs/sdd"): "config", ("fr", "envroot"): "env", ("en", ".sdd"): "default"}[(lang, root)]


# source: spec-workflow-foundation-session-config §3.1.2 sha256:d9e59c0cafd9
@pytest.mark.parametrize("has_env", [True, False])
def test_config_wins(tmp_path, monkeypatch, has_env):
    assert _resolve(tmp_path, monkeypatch, True, has_env) == "config"


# source: spec-workflow-foundation-session-config §3.1.2 sha256:d9e59c0cafd9
def test_env_wins_without_config(tmp_path, monkeypatch):
    assert _resolve(tmp_path, monkeypatch, False, True) == "env"


# source: spec-workflow-foundation-session-config §3.1.2 sha256:d9e59c0cafd9
def test_default_without_either(tmp_path, monkeypatch):
    assert _resolve(tmp_path, monkeypatch, False, False) == "default"
