"""naming.py のユニットテスト（pytest）。

命名規則の単一定義（has_spec_suffix）、書き込み前検証（validate_naming）、
ドキュメント種別判定（determine_type）を検証する。
"""

import importlib.util
import os
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "naming.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("naming", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


nm = _load_module()

REQ = os.path.join(".sdd", "requirement")
SPEC = os.path.join(".sdd", "specification")
ADR = os.path.join(".sdd", "adr")


class TestHasSpecSuffix:
    @pytest.mark.parametrize("stem,expected", [
        ("user-login_spec", True),
        ("index_design", True),
        ("user-login", False),
        ("index", False),
    ])
    def test_suffix(self, stem, expected):
        assert nm.has_spec_suffix(stem) is expected


class TestIsDesignStem:
    def test_design_suffix_detected(self):
        assert nm.is_design_stem("user-login_design") is True

    def test_spec_suffix_is_not_design(self):
        assert nm.is_design_stem("user-login_spec") is False

    def test_suffixless_is_not_design(self):
        assert nm.is_design_stem("user-login") is False


class TestFeatureName:
    def test_strips_spec_suffix(self):
        assert nm.feature_name("user-login_spec") == "user-login"

    def test_strips_design_suffix(self):
        assert nm.feature_name("user-login_design") == "user-login"

    def test_keeps_suffixless_stem(self):
        assert nm.feature_name("user-login") == "user-login"

    def test_keeps_embedded_suffix_word(self):
        # Only a trailing suffix is stripped.
        assert nm.feature_name("spec-review") == "spec-review"


class TestValidateNaming:
    def test_requirement_plain_ok(self):
        assert nm.validate_naming(os.path.join(REQ, "user-login.md"), REQ) == ""

    def test_requirement_with_suffix_violates(self):
        assert "Naming violation" in nm.validate_naming(
            os.path.join(REQ, "user-login_spec.md"), REQ
        )

    def test_specification_with_suffix_ok(self):
        assert nm.validate_naming(os.path.join(SPEC, "index_design.md"), REQ) == ""

    def test_specification_without_suffix_ok(self):
        # Suffix is optional under specification/: single-type directory, no
        # longer enforced (issue #84).
        assert nm.validate_naming(os.path.join(SPEC, "user-login.md"), REQ) == ""

    def test_adr_with_suffix_ok(self):
        assert nm.validate_naming(os.path.join(ADR, "index-decisions.md"), REQ) == ""

    def test_adr_without_suffix_ok(self):
        assert nm.validate_naming(os.path.join(ADR, "user-login.md"), REQ) == ""

    def test_non_markdown_ignored(self):
        assert nm.validate_naming(os.path.join(SPEC, "notes.txt"), REQ) == ""

    def test_outside_sdd_dirs_ignored(self):
        assert nm.validate_naming("src/main.py", REQ) == ""

    def test_requirement_ignored_by_pattern(self):
        rel = os.path.join(REQ, "user-login_spec_test.md")
        assert nm.validate_naming(rel, REQ, ("*_test.md",)) == ""

    def test_ignore_pattern_no_match_still_violates(self):
        rel = os.path.join(REQ, "user-login_spec.md")
        assert "Naming violation" in nm.validate_naming(rel, REQ, ("*_test.md",))


class TestDetermineType:
    def test_requirement_is_prd(self):
        assert nm.determine_type(
            "/p/.sdd/requirement/login.md", "login",
            "requirement", "specification", "task", "adr",
        ) == "prd"

    def test_spec(self):
        assert nm.determine_type(
            "/p/.sdd/specification/login_spec.md", "login_spec",
            "requirement", "specification", "task", "adr",
        ) == "spec"

    def test_design(self):
        assert nm.determine_type(
            "/p/.sdd/specification/login_design.md", "login_design",
            "requirement", "specification", "task", "adr",
        ) == "design"

    def test_specification_no_suffix_is_spec(self):
        # specification/ is a single-type directory (abstract specs only);
        # suffix is optional (issue #84), so an unsuffixed name is still "spec".
        assert nm.determine_type(
            "/p/.sdd/specification/notes.md", "notes",
            "requirement", "specification", "task", "adr",
        ) == "spec"

    def test_task_implementation_log(self):
        assert nm.determine_type(
            "/p/.sdd/task/impl_log.md", "impl_log",
            "requirement", "specification", "task", "adr",
        ) == "implementation-log"

    def test_task_generic(self):
        assert nm.determine_type(
            "/p/.sdd/task/notes.md", "notes",
            "requirement", "specification", "task", "adr",
        ) == "task"

    def test_unrelated_path_unknown(self):
        assert nm.determine_type(
            "/p/src/main.py", "main",
            "requirement", "specification", "task", "adr",
        ) == "unknown"

    def test_adr(self):
        assert nm.determine_type(
            "/p/.sdd/adr/login-decisions.md", "login-decisions",
            "requirement", "specification", "task", "adr",
        ) == "adr"

    def test_adr_with_custom_dir(self):
        assert nm.determine_type(
            "/p/.sdd/decisions/login.md", "login",
            "requirement", "specification", "task", "decisions",
        ) == "adr"
