"""spec-quality-guardrails-constitution-injection の点命題を実装に対して検証する差分テスト。

.sdd/laws/quality-guardrails/constitution-injection/LAWS.bend の法則（判定表 1 行ずつ）を、
参照モデル main.bend ではなく実装 pre-tool-use.py に対して assert する（laws-drafting_spec FR-014）。
テスト名は法則名に対応する。bend は不要。
"""
# spec: spec-quality-guardrails-constitution-injection
# impl-of: plugins/sdd-workflow/scripts/pre-tool-use.py

import importlib.util
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins" / "sdd-workflow" / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pre_tool_use = _load("pre_tool_use", SCRIPTS / "pre-tool-use.py")


def _injects(tmp_path, capsys, constitution_exists, is_source_code, already_injected) -> bool:
    """model-api: should_inject(constitution_exists, is_source_code, already_injected) -> Bool"""
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    if constitution_exists:
        (sdd / "CONSTITUTION.md").write_text("# C\nprinciple", encoding="utf-8")
    rel = "src/app.py" if is_source_code else "docs/readme.md"
    session_id = f"law-{uuid.uuid4().hex}"
    marker = Path(pre_tool_use.session_marker_path(session_id))
    if already_injected:
        marker.write_text("x", encoding="utf-8")
    try:
        pre_tool_use.maybe_inject_constitution(rel, str(tmp_path), ".sdd", session_id)
        out = capsys.readouterr().out
    finally:
        if marker.exists():
            marker.unlink()
    return "additionalContext" in out


# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
def test_no_constitution_means_no_injection(tmp_path, capsys):
    assert _injects(tmp_path, capsys, False, True, False) is False


# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
def test_non_source_edit_means_no_injection(tmp_path, capsys):
    assert _injects(tmp_path, capsys, True, False, False) is False


# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
def test_already_injected_means_no_injection(tmp_path, capsys):
    assert _injects(tmp_path, capsys, True, True, True) is False


# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
def test_first_source_edit_with_constitution_injects(tmp_path, capsys):
    assert _injects(tmp_path, capsys, True, True, False) is True
