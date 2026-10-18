"""laws_header.py のユニットテスト（pytest）。

Bend 法則ファイルの先頭コメント規約（# spec: / # approved: / # model-of:）の解析、
法則本文の内容ハッシュ、承認行の有効性、law 宣言、LAWS import、import allowlist を検証する
（proof-gate_spec FR-004 / FR-005、design-draft §5.4 / §8）。
"""

import hashlib
import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "laws_header.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("laws_header", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lh = _load_module()

BODY = "import Base\nimport ./main\n\nlaw sort_preserves_length:\n  (xs: List(Nat)) -> len(sort(xs)) == len(xs)\n"


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


# --- read_header -----------------------------------------------------------


class TestReadHeader:
    def test_parses_spec_and_approved(self, tmp_path):
        p = _write(tmp_path / "LAWS.bend",
                   "# spec: spec-auth-user-login\n# approved: 2026-10-17 @r sha256:abcdefabcdef\n\n" + BODY)
        h = lh.read_header(p)
        assert h["spec"] == ["spec-auth-user-login"]
        assert h["approved"] == ["2026-10-17 @r sha256:abcdefabcdef"]

    def test_model_of_multiple_lines(self, tmp_path):
        p = _write(tmp_path / "main.bend",
                   "# spec: spec-x\n# model-of: src/a.py\n# model-of: src/b.py\n\nimport Base\n")
        assert lh.read_header(p)["model-of"] == ["src/a.py", "src/b.py"]

    def test_stops_at_first_code_line(self, tmp_path):
        p = _write(tmp_path / "LAWS.bend",
                   "# spec: spec-x\n\nimport Base\n# approved: 2026-10-17 @r sha256:abcdefabcdef\n")
        h = lh.read_header(p)
        assert h["spec"] == ["spec-x"]
        assert "approved" not in h

    def test_skips_bom_and_unknown_keys_and_plain_comments(self, tmp_path):
        p = _write(tmp_path / "LAWS.bend",
                   "﻿# just a comment\n# spec: spec-x\n# author: someone\n" + BODY)
        h = lh.read_header(p)
        assert h["spec"] == ["spec-x"]
        assert "author" in h  # unknown keys are collected but ignored by callers
        assert "just" not in h

    def test_empty_file(self, tmp_path):
        p = _write(tmp_path / "LAWS.bend", "")
        assert lh.read_header(p) == {}


# --- law_body_hash ---------------------------------------------------------


class TestLawBodyHash:
    def test_excludes_leading_header(self, tmp_path):
        a = _write(tmp_path / "a" / "LAWS.bend", "# spec: spec-x\n\n" + BODY)
        b = _write(tmp_path / "b" / "LAWS.bend",
                   "# spec: spec-y\n# approved: 2026-10-17 @r sha256:000000000000\n" + BODY)
        assert lh.law_body_hash(a) == lh.law_body_hash(b)
        assert lh.law_body_hash(a) == _digest(BODY.rstrip("\n"))

    def test_changes_when_body_changes(self, tmp_path):
        a = _write(tmp_path / "a" / "LAWS.bend", "# spec: spec-x\n" + BODY)
        b = _write(tmp_path / "b" / "LAWS.bend", "# spec: spec-x\n" + BODY.replace("len(xs)", "len(xs) + 0"))
        assert lh.law_body_hash(a) != lh.law_body_hash(b)

    def test_whitespace_change_in_body_changes_hash(self, tmp_path):
        a = _write(tmp_path / "a" / "LAWS.bend", BODY)
        b = _write(tmp_path / "b" / "LAWS.bend", BODY.replace("\n\nlaw", "\nlaw"))
        assert lh.law_body_hash(a) != lh.law_body_hash(b)

    def test_is_12_hex_chars(self, tmp_path):
        p = _write(tmp_path / "LAWS.bend", BODY)
        h = lh.law_body_hash(p)
        assert len(h) == 12 and int(h, 16) >= 0


# --- valid_approval --------------------------------------------------------


class TestValidApproval:
    def test_matching_digest_is_valid(self):
        line = "2026-10-17 @reviewer sha256:abcdefabcdef"
        assert lh.valid_approval({"approved": [line]}, "abcdefabcdef") == line

    def test_digest_mismatch_is_invalid(self):
        assert lh.valid_approval({"approved": ["2026-10-17 @r sha256:abcdefabcdef"]}, "000000000000") is None

    def test_any_of_multiple_lines_may_match(self):
        new = "2026-10-18 @r sha256:111111111111"
        header = {"approved": ["2026-10-17 @r sha256:abcdefabcdef", new]}
        assert lh.valid_approval(header, "111111111111") == new

    def test_missing_approver_is_invalid(self):
        assert lh.valid_approval({"approved": ["2026-10-17 sha256:abcdefabcdef"]}, "abcdefabcdef") is None

    def test_missing_digest_is_invalid(self):
        assert lh.valid_approval({"approved": ["2026-10-17 @r"]}, "abcdefabcdef") is None

    def test_short_digest_is_invalid(self):
        assert lh.valid_approval({"approved": ["2026-10-17 @r sha256:abcdef"]}, "abcdef") is None

    def test_invalid_calendar_date_is_invalid(self):
        assert lh.valid_approval({"approved": ["2026-02-30 @r sha256:abcdefabcdef"]}, "abcdefabcdef") is None

    def test_no_approved_lines(self):
        assert lh.valid_approval({}, "abcdefabcdef") is None


# --- declares_laws / imports_laws -----------------------------------------


class TestDeclarations:
    def test_declares_laws_true(self, tmp_path):
        assert lh.declares_laws(_write(tmp_path / "LAWS.bend", BODY)) is True

    def test_declares_laws_false(self, tmp_path):
        p = _write(tmp_path / "LAWS.bend", "# spec: spec-x\nimport Base\n# law commented out\ndef lawful: 1\n")
        assert lh.declares_laws(p) is False

    def test_imports_laws_spellings(self, tmp_path):
        for text in ("import ./LAWS.bend as Laws\n", "import LAWS.bend as L\n", "  import ./LAWS.bend  as  Laws_1  \n"):
            assert lh.imports_laws(_write(tmp_path / "PROOF.bend", text)) is True

    def test_imports_laws_false(self, tmp_path):
        assert lh.imports_laws(_write(tmp_path / "PROOF.bend", "import Base\nimport ./main.bend as Model\n")) is False

    def test_imports_laws_without_alias_or_extension_is_false(self, tmp_path):
        # Bend 2.0.37 rejects these as syntax errors, so they never count as importing LAWS.
        for text in ("import ./LAWS\n", "import ./LAWS.bend\n", "import LAWS\n", "import ./LAWS as Laws\n",
                     "import ./LAWS.bend as Laws # laws\n", "import ./LAWS.bend as La-ws\n"):
            assert lh.imports_laws(_write(tmp_path / "PROOF.bend", text)) is False


# --- disallowed_imports ----------------------------------------------------


class TestDisallowedImports:
    def _laws_dir(self, tmp_path):
        d = tmp_path / "laws" / "f"
        _write(d / "LAWS.bend", "import Base\nimport ./main.bend as Model\nlaw a: 1\n")
        _write(d / "main.bend", "import Base\n")
        _write(d / "PROOF.bend", "import Base\nimport ./LAWS.bend as Laws\nimport ./main.bend as Model\n")
        return d

    def test_clean_directory(self, tmp_path):
        assert lh.disallowed_imports(self._laws_dir(tmp_path)) == []

    def test_dot_slash_optional_and_alias_spacing_and_charset(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend", "import LAWS.bend as L\nimport ./main.bend  as  Model_2\n")
        assert lh.disallowed_imports(d) == []

    def test_local_import_without_alias_rejected(self, tmp_path):
        # The pre-#162 allowlist accepted these; Bend 2.0.37 does not (syntax error).
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend", "import ./LAWS.bend\nimport ./main\nimport LAWS\n")
        assert len(lh.disallowed_imports(d)) == 3

    def test_local_import_without_bend_extension_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend", "import ./LAWS as Laws\nimport ./main as Model\n")
        assert len(lh.disallowed_imports(d)) == 2

    def test_bad_alias_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend", "import ./main.bend as M-x\nimport ./main.bend as M.x\nimport ./main.bend as\n")
        assert len(lh.disallowed_imports(d)) == 3

    def test_base_with_alias_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend", "import Base as B\n")
        assert lh.disallowed_imports(d) == ["PROOF.bend: import Base as B"]

    def test_nonexistent_file_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend", "import ./LAWS.bend as Laws\nimport ./missing.bend as Missing\n")
        assert lh.disallowed_imports(d) == ["PROOF.bend: import ./missing.bend as Missing"]

    def test_hub_import_forms_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend",
               "import 0x1234abcd/main.bend as P\nimport foo@1.0.0.0/main.bend as Q\nimport SomePkg\n")
        assert len(lh.disallowed_imports(d)) == 3

    def test_parent_absolute_namespace_url_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend",
               "import ./LAWS.bend as Laws\nimport ../other.bend as O\nimport /abs/path.bend as A\n"
               "import @hub/pkg.bend as H\nimport https://x.y/z.bend as U\n")
        bad = lh.disallowed_imports(d)
        assert len(bad) == 4
        assert all(b.startswith("PROOF.bend: import ") for b in bad)

    def test_trailing_comment_and_from_forms_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "PROOF.bend",
               "import ./LAWS.bend as Laws # laws\nimport Base # std\nfrom ./main.bend import sort\n")
        assert len(lh.disallowed_imports(d)) == 3

    def test_subdirectory_recursion_and_relative_resolution(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(d / "lib" / "helper.bend", "import Base\n")
        _write(d / "lib" / "util.bend",
               "import Base\nimport ./helper.bend as H\nimport ../main.bend as M\nimport ./missing.bend as X\n")
        _write(d / "PROOF.bend", "import ./LAWS.bend as Laws\nimport ./lib/util.bend as U\n")
        bad = lh.disallowed_imports(d)
        # ./helper exists next to util.bend; `..` is never allowed even when it
        # would stay inside the laws directory; ./missing does not exist.
        assert bad == [str(Path("lib") / "util.bend") + ": import ../main.bend as M",
                       str(Path("lib") / "util.bend") + ": import ./missing.bend as X"]

    def test_escape_via_subdirectory_dotdot_rejected(self, tmp_path):
        d = self._laws_dir(tmp_path)
        _write(tmp_path / "laws" / "outside.bend", "import Base\n")
        _write(d / "lib" / "util.bend", "import ../../outside.bend as O\n")
        assert lh.disallowed_imports(d) == [str(Path("lib") / "util.bend") + ": import ../../outside.bend as O"]

    def test_missing_directory(self, tmp_path):
        assert lh.disallowed_imports(tmp_path / "nope") == []
