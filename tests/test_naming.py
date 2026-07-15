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


class TestHasSpecSuffix:
    @pytest.mark.parametrize("stem,expected", [
        ("user-login_spec", True),
        ("index_design", True),
        ("user-login", False),
        ("index", False),
    ])
    def test_suffix(self, stem, expected):
        assert nm.has_spec_suffix(stem) is expected


class TestValidateNaming:
    def test_requirement_plain_ok(self):
        assert nm.validate_naming(os.path.join(REQ, "user-login.md"), REQ, SPEC) == ""

    def test_requirement_with_suffix_violates(self):
        assert "Naming violation" in nm.validate_naming(
            os.path.join(REQ, "user-login_spec.md"), REQ, SPEC
        )

    def test_specification_with_suffix_ok(self):
        assert nm.validate_naming(os.path.join(SPEC, "index_design.md"), REQ, SPEC) == ""

    def test_specification_without_suffix_violates(self):
        assert "Naming violation" in nm.validate_naming(
            os.path.join(SPEC, "user-login.md"), REQ, SPEC
        )

    def test_non_markdown_ignored(self):
        assert nm.validate_naming(os.path.join(SPEC, "notes.txt"), REQ, SPEC) == ""

    def test_outside_sdd_dirs_ignored(self):
        assert nm.validate_naming("src/main.py", REQ, SPEC) == ""


class TestDetermineType:
    def test_requirement_is_prd(self):
        assert nm.determine_type(
            "/p/.sdd/requirement/login.md", "login",
            "requirement", "specification", "task",
        ) == "prd"

    def test_spec(self):
        assert nm.determine_type(
            "/p/.sdd/specification/login_spec.md", "login_spec",
            "requirement", "specification", "task",
        ) == "spec"

    def test_design(self):
        assert nm.determine_type(
            "/p/.sdd/specification/login_design.md", "login_design",
            "requirement", "specification", "task",
        ) == "design"

    def test_specification_unknown_suffix(self):
        assert nm.determine_type(
            "/p/.sdd/specification/notes.md", "notes",
            "requirement", "specification", "task",
        ) == "unknown"

    def test_task_implementation_log(self):
        assert nm.determine_type(
            "/p/.sdd/task/impl_log.md", "impl_log",
            "requirement", "specification", "task",
        ) == "implementation-log"

    def test_task_generic(self):
        assert nm.determine_type(
            "/p/.sdd/task/notes.md", "notes",
            "requirement", "specification", "task",
        ) == "task"

    def test_unrelated_path_unknown(self):
        assert nm.determine_type(
            "/p/src/main.py", "main",
            "requirement", "specification", "task",
        ) == "unknown"
