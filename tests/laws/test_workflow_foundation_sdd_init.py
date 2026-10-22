"""spec-workflow-foundation-sdd-init の点命題を実装に対して検証する差分テスト。

.sdd/laws/workflow-foundation/sdd-init/LAWS.bend の法則を実装 update-claude-md.py（サブプロセス実行）に対して
assert する（laws-drafting_spec FR-014）。モデル API は claude_md_action(has_section, version_match) -> Nat
（0=append 1=skip 2=replace）。bend は不要。
"""
# spec: spec-workflow-foundation-sdd-init
# impl-of: plugins/sdd-workflow/skills/sdd-init/scripts/update-claude-md.py

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins" / "sdd-workflow"
UPDATE = PLUGIN / "skills" / "sdd-init" / "scripts" / "update-claude-md.py"
PLUGIN_VERSION = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]


def _claude_md_action(tmp_path, has_section, version_match, exists=True):
    claude_md = tmp_path / "CLAUDE.md"
    before = "# Project\n\nhello\n"
    if exists:
        if has_section:
            v = PLUGIN_VERSION if version_match else "0.0.1"
            before += f"\n## AI-SDD Instructions (v{v})\n\nold body\n"
        claude_md.write_text(before, encoding="utf-8")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path), CLAUDE_PLUGIN_ROOT=str(PLUGIN))
    env.pop("SDD_LANG", None)
    r = subprocess.run([sys.executable, str(UPDATE)], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    after = claude_md.read_text(encoding="utf-8")
    if "up to date" in r.stdout:
        return "skip"
    if "Updated" in r.stdout:
        assert "old body" not in after and f"v{PLUGIN_VERSION}" in after
        return "replace"
    if "Appended" in r.stdout or "Created" in r.stdout:
        assert f"v{PLUGIN_VERSION}" in after
        if exists:
            assert after.startswith(before.rstrip("\n"))
        return "append"
    raise AssertionError(r.stdout)


# source: spec-workflow-foundation-sdd-init §3.1.1 sha256:e106785a632c
@pytest.mark.parametrize("version_match", [True, False])
def test_no_section_appends(tmp_path, version_match):
    assert _claude_md_action(tmp_path, False, version_match) == "append"


# source: spec-workflow-foundation-sdd-init §3.1.1 sha256:e106785a632c
def test_no_section_no_file_creates(tmp_path):
    # 法則外だが has_section=False の派生ケース（CLAUDE.md 自体が無い）
    assert _claude_md_action(tmp_path, False, True, exists=False) == "append"


# source: spec-workflow-foundation-sdd-init §3.1.1 sha256:e106785a632c
def test_same_version_skips(tmp_path):
    assert _claude_md_action(tmp_path, True, True) == "skip"


# source: spec-workflow-foundation-sdd-init §3.1.1 sha256:e106785a632c
def test_version_mismatch_replaces(tmp_path):
    assert _claude_md_action(tmp_path, True, False) == "replace"
