"""spec-quality-guardrails-naming-enforcement の点命題を実装に対して検証する差分テスト。

naming-enforcement_spec 3.1.1 の判定表（旧 .sdd/laws/quality-guardrails/naming-enforcement/ の点命題）を
実装 naming.py に対して assert する（laws-drafting_spec FR-014）。モデル API は decide(is_md, ignore_match, is_requirement_dir, has_suffix) -> Nat
（0=allow(not .md) 1=allow(ignore) 2=deny 3=allow(fallthrough)）だが、実装は allow を空文字列、deny を
非空文字列で返すため 0/1/3 は区別できない。allow / deny として検証する。bend は不要。
"""
# spec: spec-quality-guardrails-naming-enforcement
# impl-of: plugins/sdd-workflow/scripts/naming.py

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "plugins" / "sdd-workflow" / "scripts"))

import naming  # noqa: E402

REQ = ".sdd/requirement"


def _decide(is_md, ignore_match, is_requirement_dir, has_suffix):
    stem = "user-login_spec" if has_suffix else "user-login"
    ext = ".md" if is_md else ".txt"
    d = REQ if is_requirement_dir else ".sdd/specification"
    rel = f"{d}/{stem}{ext}"
    patterns = (f"{stem}{ext}",) if ignore_match else ()
    return "deny" if naming.validate_naming(rel, REQ, patterns) else "allow"


# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
def test_non_md_is_allowed():
    assert _decide(False, False, False, False) == "allow"


# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
def test_ignore_pattern_match_is_allowed():
    assert _decide(True, True, True, True) == "allow"


# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
def test_requirement_with_suffix_is_denied():
    assert _decide(True, False, True, True) == "deny"


# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
def test_requirement_without_suffix_is_allowed():
    assert _decide(True, False, True, False) == "allow"


# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
def test_non_requirement_dir_is_allowed():
    assert _decide(True, False, False, True) == "allow"
