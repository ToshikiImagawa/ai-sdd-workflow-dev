"""detect-references.py のユニットテスト（pytest）。

移行対象の列挙、参照の分類（コア標準 / プロジェクト固有）、design-draft の
誤検出防止、触らないファイルの除外、custom root 配下の .cache 生成、
CLAUDE_ENV_FILE エクスポートを検証する。
"""

import importlib.util
import json
import os
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins"
    / "sdd-workflow"
    / "skills"
    / "migrate-design-to-adr"
    / "scripts"
    / "detect-references.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("detect_references", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dr = _load_module()


# --- is_untouchable --------------------------------------------------------


class TestIsUntouchable:
    @pytest.mark.parametrize(
        "rel_path",
        [
            "AI-SDD-PRINCIPLES.md",
            "MIGRATION_PENDING.md",
            "UPDATE_REQUIRED.md",
            "CHANGELOG.md",
            "specification/CHANGELOG.md",
            ".cache/migrate-design-to-adr/reference_detection.json",
        ],
    )
    def test_generated_and_historical_files(self, rel_path):
        assert dr.is_untouchable(rel_path) is True

    @pytest.mark.parametrize(
        "rel_path",
        ["specification/user-auth_spec.md", "requirement/user-auth.md", "src/app.py"],
    )
    def test_regular_files(self, rel_path):
        assert dr.is_untouchable(rel_path) is False


# --- is_design_draft_reference --------------------------------------------


class TestIsDesignDraftReference:
    @pytest.mark.parametrize(
        "token",
        [
            "task/123/design-draft.md",
            "[draft](../task/123/design-draft.md)",
            "design-draft.md",
            "design-123",
            "design-TICKET-123",
        ],
    )
    def test_v5_draft_records(self, token):
        assert dr.is_design_draft_reference(token) is True

    @pytest.mark.parametrize(
        "token", ["user-auth_design.md", "design-user-auth", "design-auth-v2"]
    )
    def test_migration_targets(self, token):
        assert dr.is_design_draft_reference(token) is False


# --- find_matches ----------------------------------------------------------


class TestFindMatches:
    def test_path_match_without_boundary(self):
        line = "see user-auth_design.md and user-auth_design.md again"
        assert len(list(dr.find_matches(line, "user-auth_design.md", False))) == 2

    def test_id_match_requires_boundary(self):
        line = 'depends-on: ["design-user-auth"]'
        assert len(list(dr.find_matches(line, "design-user-auth", True))) == 1

    def test_id_match_rejects_longer_id(self):
        line = 'depends-on: ["design-user-auth-extra"]'
        assert list(dr.find_matches(line, "design-user-auth", True)) == []


# --- matched_token ---------------------------------------------------------


class TestMatchedToken:
    def test_returns_whitespace_delimited_token(self):
        line = "- link: [draft](task/1/design-draft.md) here"
        start = line.index("design-draft.md")
        token = dr.matched_token(line, start, start + len("design-draft.md"))
        assert token == "[draft](task/1/design-draft.md)"


# --- hierarchical_id ------------------------------------------------------


class TestHierarchicalId:
    def test_flat_layout(self):
        assert dr.hierarchical_id("adr", Path("."), "user-auth") == "adr-user-auth"

    def test_hierarchical_layout(self):
        assert dr.hierarchical_id("design", Path("auth"), "user-login") == "design-auth-user-login"


# --- classify --------------------------------------------------------------


class _Paths:
    """Stand-in for hook_common.SddPaths with the default directory names."""

    root = ".sdd"
    requirement_dir = "requirement"
    specification_dir = "specification"
    adr_dir = "adr"
    task_dir = "task"


class TestClassify:
    def _classify(self, rel_path, line, in_fm=False, fm_key="", ignore_patterns=()):
        return dr.classify(rel_path, line, in_fm, fm_key, _Paths(), ignore_patterns)

    def test_spec_link_is_core_standard(self):
        category, kind = self._classify(
            "specification/user-auth_spec.md", "関連 Design Doc: [設計](user-auth_design.md)"
        )
        assert (category, kind) == (dr.CORE_STANDARD, "spec_related_design_link")

    def test_spec_prose_is_project_specific(self):
        category, kind = self._classify(
            "specification/user-auth_spec.md", "本文で user-auth_design.md に言及する"
        )
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "spec_prose_mention")

    def test_depends_on_is_core_standard(self):
        category, kind = self._classify(
            "specification/user-auth_spec.md",
            'depends-on: ["design-user-auth"]',
            in_fm=True,
            fm_key="depends-on",
        )
        assert (category, kind) == (dr.CORE_STANDARD, "front_matter_depends_on")

    def test_custom_front_matter_field_is_project_specific(self):
        category, kind = self._classify(
            "specification/user-auth_spec.md",
            "source_design: user-auth_design.md",
            in_fm=True,
            fm_key="source_design",
        )
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "custom_front_matter_field")

    def test_prd_link_line_is_core_standard(self):
        category, kind = self._classify(
            "requirement/user-auth.md", "- 設計: [design](../specification/user-auth_design.md)"
        )
        assert (category, kind) == (dr.CORE_STANDARD, "prd_design_link")

    def test_prd_prose_is_project_specific(self):
        category, kind = self._classify(
            "requirement/user-auth.md", "FR-001 は user-auth_design.md に従う"
        )
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "prd_prose_mention")

    def test_declared_ignore_pattern_is_custom_document_type(self):
        category, kind = self._classify(
            "specification/user-auth_spec-test.md",
            "[design](user-auth_design.md)",
            ignore_patterns=("*_spec-test.md",),
        )
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "custom_document_type")

    def test_undeclared_suffix_is_custom_document_type(self):
        category, kind = self._classify(
            "specification/user-auth_spec-test.md", "[design](user-auth_design.md)"
        )
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "custom_document_type")

    def test_adr_reference_is_project_specific(self):
        category, kind = self._classify("adr/user-auth.md", "移行元: user-auth_design.md")
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "adr_reference")

    def test_task_reference_is_project_specific(self):
        category, kind = self._classify("task/123/tasks.md", "[design](../../specification/user-auth_design.md)")
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "task_reference")

    def test_code_comment_is_project_specific(self):
        category, kind = self._classify("src/app.py", "# see specification/user-auth_design.md")
        assert (category, kind) == (dr.PROJECT_SPECIFIC, "code_comment")


# --- end-to-end -----------------------------------------------------------


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def project(tmp_path):
    """A project with one v4.x design doc and references of every category."""
    root = tmp_path / "proj"
    sdd = root / ".sdd"
    _write(root / ".sdd-config.json", json.dumps({"root": ".sdd", "lang": "ja"}))
    _write(
        sdd / "specification" / "user-auth_design.md",
        "---\nid: design-user-auth\ntype: design\n---\n# design\n",
    )
    _write(
        sdd / "specification" / "user-auth_spec.md",
        "---\n"
        'id: spec-user-auth\n'
        'depends-on: ["prd-user-auth", "design-user-auth"]\n'
        "source_design: user-auth_design.md\n"
        "---\n"
        "# spec\n"
        "関連 Design Doc: [技術設計書](user-auth_design.md)\n"
        "本文で user-auth_design.md を言及する行。\n"
        "ドラフトは task/123/design-draft.md と design-123 を使う。\n",
    )
    _write(
        sdd / "requirement" / "user-auth.md",
        "# PRD\n"
        "- 設計: [design](../specification/user-auth_design.md)\n"
        "FR-001 は user-auth_design.md に従う\n",
    )
    _write(sdd / "AI-SDD-PRINCIPLES.md", "user-auth_design.md\n")
    _write(sdd / "MIGRATION_PENDING.md", "user-auth_design.md\n")
    _write(root / "src" / "app.py", "# see specification/user-auth_design.md\n")
    return root


def _run(project_root: Path, argv: list, monkeypatch, env_file: Path = None, sdd_root: str = ".sdd"):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_root))
    if env_file is not None:
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
    else:
        monkeypatch.delenv("CLAUDE_ENV_FILE", raising=False)
    monkeypatch.chdir(project_root)
    dr.main(argv)
    result = project_root / sdd_root / ".cache" / "migrate-design-to-adr" / "reference_detection.json"
    return json.loads(result.read_text(encoding="utf-8"))


class TestEndToEnd:
    def test_target_and_adr_paths(self, project, monkeypatch):
        data = _run(project, ["--all"], monkeypatch)
        assert data["total_targets"] == 1
        target = data["targets"][0]
        assert target["feature"] == "user-auth"
        assert target["design_relative_path"] == os.path.join("specification", "user-auth_design.md")
        assert target["adr_relative_path"] == os.path.join("adr", "user-auth.md")
        assert target["adr_id"] == "adr-user-auth"
        assert target["design_id"] == "design-user-auth"

    def test_classification_counts(self, project, monkeypatch):
        data = _run(project, ["--all"], monkeypatch)
        target = data["targets"][0]
        kinds = {(r["category"], r["kind"]) for r in target["references"]}
        assert (dr.CORE_STANDARD, "spec_related_design_link") in kinds
        assert (dr.CORE_STANDARD, "front_matter_depends_on") in kinds
        assert (dr.CORE_STANDARD, "prd_design_link") in kinds
        assert (dr.PROJECT_SPECIFIC, "custom_front_matter_field") in kinds
        assert (dr.PROJECT_SPECIFIC, "prd_prose_mention") in kinds
        assert (dr.PROJECT_SPECIFIC, "code_comment") in kinds
        assert target["core_standard_count"] == 3
        assert target["project_specific_count"] + target["core_standard_count"] == len(
            target["references"]
        )

    def test_design_draft_is_not_detected(self, project, monkeypatch):
        data = _run(project, ["--all"], monkeypatch)
        texts = [r["text"] for r in data["targets"][0]["references"]]
        assert not any("design-draft" in t for t in texts)
        assert not any("design-123" in t for t in texts)

    def test_generated_files_are_excluded(self, project, monkeypatch):
        data = _run(project, ["--all"], monkeypatch)
        paths = {r["path"] for r in data["targets"][0]["references"]}
        assert "AI-SDD-PRINCIPLES.md" not in paths
        assert "MIGRATION_PENDING.md" not in paths

    def test_design_doc_itself_is_not_a_reference(self, project, monkeypatch):
        data = _run(project, ["--all"], monkeypatch)
        paths = {r["path"] for r in data["targets"][0]["references"]}
        assert os.path.join("specification", "user-auth_design.md") not in paths

    def test_docs_only_skips_code(self, project, monkeypatch):
        data = _run(project, ["--all", "--docs-only"], monkeypatch)
        paths = {r["path"] for r in data["targets"][0]["references"]}
        assert not any(p.endswith("app.py") for p in paths)

    def test_feature_filter(self, project, monkeypatch):
        _write(
            project / ".sdd" / "specification" / "billing_design.md",
            "---\nid: design-billing\n---\n# design\n",
        )
        data = _run(project, ["user-auth"], monkeypatch)
        assert data["mode"] == "single"
        assert [t["feature"] for t in data["targets"]] == ["user-auth"]

    def test_hierarchical_layout(self, project, monkeypatch):
        _write(
            project / ".sdd" / "specification" / "auth" / "user-login_design.md",
            "---\nid: design-auth-user-login\n---\n# design\n",
        )
        data = _run(project, ["user-login"], monkeypatch)
        target = data["targets"][0]
        assert target["design_id"] == "design-auth-user-login"
        assert target["adr_relative_path"] == os.path.join("adr", "auth", "user-login.md")

    def test_custom_root_cache_and_env_export(self, tmp_path, monkeypatch):
        root = tmp_path / "custom"
        _write(root / ".sdd-config.json", json.dumps({"root": "docs-sdd", "lang": "en"}))
        _write(
            root / "docs-sdd" / "specification" / "user-auth_design.md",
            "---\nid: design-user-auth\n---\n# design\n",
        )
        env_file = tmp_path / "env.sh"
        data = _run(root, ["--all"], monkeypatch, env_file=env_file, sdd_root="docs-sdd")
        assert data["total_targets"] == 1
        assert (root / "docs-sdd" / ".cache" / "migrate-design-to-adr" / "reference_detection.json").is_file()
        exported = env_file.read_text(encoding="utf-8")
        assert "MIGRATE_ADR_CACHE_DIR" in exported
        assert "MIGRATE_ADR_DETECTION_RESULT" in exported

    def test_no_arguments_exits_with_usage_error(self):
        with pytest.raises(SystemExit) as excinfo:
            dr.main([])
        assert excinfo.value.code == 2
