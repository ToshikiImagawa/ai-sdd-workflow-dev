"""doc_walker.py のユニットテスト（pytest）。

対象選択ルール（requirement=全.md / specification=全.md（サフィックス任意） / task=全.md）と
spec 探索を検証する。
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "doc_walker.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("doc_walker", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dw = _load_module()


def _seed(base: Path):
    (base / ".sdd" / "requirement" / "nested").mkdir(parents=True)
    (base / ".sdd" / "specification").mkdir(parents=True)
    (base / ".sdd" / "task").mkdir(parents=True)
    (base / ".sdd" / "adr").mkdir(parents=True)
    (base / ".sdd" / "requirement" / "index.md").write_text("# i", encoding="utf-8")
    (base / ".sdd" / "requirement" / "nested" / "child.md").write_text("# c", encoding="utf-8")
    (base / ".sdd" / "specification" / "a_spec.md").write_text("# s", encoding="utf-8")
    (base / ".sdd" / "specification" / "a_design.md").write_text("# d", encoding="utf-8")
    (base / ".sdd" / "specification" / "notes.md").write_text("# n", encoding="utf-8")
    (base / ".sdd" / "task" / "log.md").write_text("# l", encoding="utf-8")
    (base / ".sdd" / "adr" / "user-login-decisions.md").write_text("# a", encoding="utf-8")


class TestIterTargetFiles:
    def test_requirement_and_specification_all_md(self, tmp_path):
        _seed(tmp_path)
        targets = dw.iter_target_files(str(tmp_path), ".sdd", "requirement", "specification", "adr")
        names = sorted(Path(p).name for p in targets)
        # requirement: index.md, child.md; specification: every .md, suffix optional;
        # adr: every .md, suffix optional; no task
        assert names == [
            "a_design.md", "a_spec.md", "child.md", "index.md", "notes.md",
            "user-login-decisions.md",
        ]

    def test_globally_sorted_strings(self, tmp_path):
        _seed(tmp_path)
        targets = dw.iter_target_files(str(tmp_path), ".sdd", "requirement", "specification", "adr")
        assert targets == sorted(targets)

    def test_missing_dirs_returns_empty(self, tmp_path):
        assert dw.iter_target_files(str(tmp_path), ".sdd", "requirement", "specification", "adr") == []


class TestCollectDocuments:
    def test_includes_task_and_section_order(self, tmp_path):
        _seed(tmp_path)
        docs = dw.collect_documents(tmp_path / ".sdd", "requirement", "specification", "task", "adr")
        names = sorted(p.name for p in docs)
        assert names == [
            "a_design.md", "a_spec.md", "child.md", "index.md", "log.md", "notes.md",
            "user-login-decisions.md",
        ]

    def test_specification_includes_plain_md(self, tmp_path):
        # Suffix is optional under specification/ (issue #84).
        _seed(tmp_path)
        docs = dw.collect_documents(tmp_path / ".sdd", "requirement", "specification", "task", "adr")
        assert "notes.md" in [p.name for p in docs]

    def test_adr_included_with_suffix_optional(self, tmp_path):
        _seed(tmp_path)
        docs = dw.collect_documents(tmp_path / ".sdd", "requirement", "specification", "task", "adr")
        assert "user-login-decisions.md" in [p.name for p in docs]


class TestFindSpecDoc:
    def test_finds_suffixed_spec_recursively(self, tmp_path):
        spec = tmp_path / "spec" / "auth"
        spec.mkdir(parents=True)
        target = spec / "user-login_spec.md"
        target.write_text("# s", encoding="utf-8")
        assert dw.find_spec_doc(str(tmp_path / "spec"), "user-login") == str(target)

    def test_finds_suffixless_spec(self, tmp_path):
        # The _spec suffix is optional under specification/ (issue #84).
        spec = tmp_path / "spec" / "auth"
        spec.mkdir(parents=True)
        target = spec / "user-login.md"
        target.write_text("# s", encoding="utf-8")
        assert dw.find_spec_doc(str(tmp_path / "spec"), "user-login") == str(target)

    def test_suffixed_spec_wins_over_suffixless(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        (spec / "user-login.md").write_text("# plain", encoding="utf-8")
        suffixed = spec / "user-login_spec.md"
        suffixed.write_text("# s", encoding="utf-8")
        assert dw.find_spec_doc(str(spec), "user-login") == str(suffixed)

    def test_design_doc_never_matches(self, tmp_path):
        # A v4.x design doc is not a spec, so it is not a spec sync target
        # (find_legacy_design_doc locates it instead).
        spec = tmp_path / "spec"
        spec.mkdir()
        (spec / "user-login_design.md").write_text("# d", encoding="utf-8")
        assert dw.find_spec_doc(str(spec), "user-login") == ""

    def test_deterministic_when_stem_collides(self, tmp_path):
        spec = tmp_path / "spec"
        (spec / "b").mkdir(parents=True)
        (spec / "a").mkdir()
        (spec / "b" / "dup_spec.md").write_text("# b", encoding="utf-8")
        (spec / "a" / "dup_spec.md").write_text("# a", encoding="utf-8")
        assert dw.find_spec_doc(str(spec), "dup") == str(spec / "a" / "dup_spec.md")

    def test_returns_empty_when_absent(self, tmp_path):
        (tmp_path / "spec").mkdir()
        assert dw.find_spec_doc(str(tmp_path / "spec"), "missing") == ""

    def test_stem_with_glob_metacharacters_matches_literally(self, tmp_path):
        # A source file named e.g. parse[v2].py has stem "parse[v2]"; the
        # brackets must be matched literally, not treated as an fnmatch
        # character class (which would make "[v2]" match a single "v"/"2").
        spec = tmp_path / "spec"
        spec.mkdir()
        target = spec / "parse[v2]_spec.md"
        target.write_text("# s", encoding="utf-8")
        assert dw.find_spec_doc(str(spec), "parse[v2]") == str(target)


class TestFindLegacyDesignDoc:
    def test_finds_v4_design_doc_recursively(self, tmp_path):
        spec = tmp_path / "spec" / "auth"
        spec.mkdir(parents=True)
        target = spec / "user-login_design.md"
        target.write_text("# d", encoding="utf-8")
        assert dw.find_legacy_design_doc(str(tmp_path / "spec"), "user-login") == str(
            target
        )

    def test_ignores_spec_and_plain_md(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        (spec / "user-login_spec.md").write_text("# s", encoding="utf-8")
        (spec / "user-login.md").write_text("# p", encoding="utf-8")
        assert dw.find_legacy_design_doc(str(spec), "user-login") == ""

    def test_deterministic_when_stem_collides(self, tmp_path):
        spec = tmp_path / "spec"
        (spec / "b").mkdir(parents=True)
        (spec / "a").mkdir()
        (spec / "b" / "dup_design.md").write_text("# b", encoding="utf-8")
        (spec / "a" / "dup_design.md").write_text("# a", encoding="utf-8")
        assert dw.find_legacy_design_doc(str(spec), "dup") == str(
            spec / "a" / "dup_design.md"
        )

    def test_returns_empty_when_absent(self, tmp_path):
        (tmp_path / "spec").mkdir()
        assert dw.find_legacy_design_doc(str(tmp_path / "spec"), "missing") == ""

    def test_stem_with_glob_metacharacters_matches_literally(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        target = spec / "parse[v2]_design.md"
        target.write_text("# d", encoding="utf-8")
        assert dw.find_legacy_design_doc(str(spec), "parse[v2]") == str(target)


class TestFindSpecOrLegacyDesignDoc:
    """One walk, same classification as find_spec_doc + find_legacy_design_doc."""

    def test_returns_spec_and_empty_design(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        target = spec / "user-login_spec.md"
        target.write_text("# s", encoding="utf-8")
        assert dw.find_spec_or_legacy_design_doc(str(spec), "user-login") == (
            str(target), "",
        )

    def test_suffixed_spec_wins_over_suffixless(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        (spec / "user-login.md").write_text("# plain", encoding="utf-8")
        suffixed = spec / "user-login_spec.md"
        suffixed.write_text("# s", encoding="utf-8")
        spec_path, design_path = dw.find_spec_or_legacy_design_doc(str(spec), "user-login")
        assert spec_path == str(suffixed)
        assert design_path == ""

    def test_returns_empty_spec_and_design_when_only_design_doc_exists(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        design = spec / "user-login_design.md"
        design.write_text("# d", encoding="utf-8")
        assert dw.find_spec_or_legacy_design_doc(str(spec), "user-login") == (
            "", str(design),
        )

    def test_returns_both_empty_when_absent(self, tmp_path):
        (tmp_path / "spec").mkdir()
        assert dw.find_spec_or_legacy_design_doc(str(tmp_path / "spec"), "missing") == (
            "", "",
        )

    def test_stem_with_glob_metacharacters_matches_literally(self, tmp_path):
        spec = tmp_path / "spec"
        spec.mkdir()
        target = spec / "parse[v2]_spec.md"
        target.write_text("# s", encoding="utf-8")
        assert dw.find_spec_or_legacy_design_doc(str(spec), "parse[v2]") == (
            str(target), "",
        )


class TestIterLegacyDesignDocs:
    def test_collects_only_design_docs_sorted(self, tmp_path):
        _seed(tmp_path)
        nested = tmp_path / ".sdd" / "specification" / "auth"
        nested.mkdir()
        (nested / "b_design.md").write_text("# d", encoding="utf-8")
        found = dw.iter_legacy_design_docs(tmp_path / ".sdd" / "specification")
        assert [p.name for p in found] == ["a_design.md", "b_design.md"]

    def test_missing_dir_returns_empty(self, tmp_path):
        assert dw.iter_legacy_design_docs(tmp_path / "nope") == []
