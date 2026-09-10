"""check-spec / constitution のヘルパースクリプトのユニットテスト（pytest）。

scripts/test-skill-scripts.sh の custom-root 回帰テストを補完し、
find-spec-docs.py / validate-files.py の関数単位・E2E 挙動を検証する:
  - custom root 配下への .cache 生成
  - フラット / 階層 / 部分一致での spec 文書検出（サフィックス有無の両方）
  - design doc が 0 件でも spec 一覧が出力されること
  - design draft の任意入力としての取り込みと、対象チケットへの絞り込み
    （`--ticket` / `--ticket=` の両書式、front matter の depends-on、単一ドラフト、
    絞り込み根拠が無い複数ドラフトの unscoped 扱い）
  - adr（決定ログ）の帰属解決（サフィックス無し / legacy `-decisions` / 階層構造の
    名前一致、名前一致が無い場合の front matter depends-on フォールバック、
    不在時の `none` がエラーにならないこと、custom な adr ディレクトリ名）
  - 引数パース（フラグを機能名と誤認しない）
  - file_mapping.json / scan_summary.json の内容
  - CLAUDE_ENV_FILE への環境変数エクスポート
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = (
    Path(__file__).resolve().parent.parent / "plugins" / "sdd-workflow"
)
FIND_SPEC = (
    PLUGIN_ROOT / "skills" / "check-spec" / "scripts" / "find-spec-docs.py"
)
VALIDATE_FILES = (
    PLUGIN_ROOT / "skills" / "constitution" / "scripts" / "validate-files.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fs = _load_module("find_spec_docs", FIND_SPEC)
vf = _load_module("validate_files", VALIDATE_FILES)


ROOT = ".ai-docs"


def _make_project(tmp_path: Path) -> Path:
    """custom root を持つ最小 SDD プロジェクトを構築する"""
    proj = tmp_path / "project"
    (proj / ROOT / "requirement").mkdir(parents=True)
    (proj / ROOT / "specification").mkdir(parents=True)
    config = {
        "root": ROOT,
        "lang": "en",
        "directories": {
            "requirement": "requirement",
            "specification": "specification",
            "task": "task",
        },
    }
    (proj / ".sdd-config.json").write_text(
        json.dumps(config), encoding="utf-8"
    )
    return proj


@pytest.fixture
def proj_env(tmp_path):
    """custom root プロジェクトと空の CLAUDE_ENV_FILE を用意する"""
    proj = _make_project(tmp_path)
    env_file = tmp_path / "env"
    env_file.write_text("", encoding="utf-8")
    return proj, env_file


def _run(script: Path, proj: Path, env_file: Path, *args) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(proj)
    env["CLAUDE_ENV_FILE"] = str(env_file)
    return subprocess.run(
        [sys.executable, str(script), *args],
        env=env,
        capture_output=True,
        text=True,
    )


# --- helper functions -----------------------------------------------------

class TestReadConfig:
    def test_defaults_when_missing_keys(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text("{}", encoding="utf-8")
        assert fs.read_config(tmp_path) == fs.SddPaths()

    def test_missing_config_falls_back_to_defaults(self, tmp_path):
        assert fs.read_config(tmp_path) == fs.SddPaths()


class TestSortedDocs:
    def test_sorted_unique_and_excludes_design_docs(self, tmp_path):
        (tmp_path / "b").mkdir()
        (tmp_path / "b" / "z_spec.md").write_text("", encoding="utf-8")
        (tmp_path / "a.md").write_text("", encoding="utf-8")
        (tmp_path / "legacy_design.md").write_text("", encoding="utf-8")
        paths = list(tmp_path.rglob("*.md")) + [tmp_path / "a.md"]
        result = fs.sorted_docs(paths)
        assert result == sorted(result)
        assert [Path(p).name for p in result] == ["a.md", "z_spec.md"]


class TestFindDesignDrafts:
    def test_missing_task_dir_is_not_an_error(self, tmp_path):
        assert fs.find_design_drafts(tmp_path / "nope") == []

    def test_collects_ticket_scoped_drafts_sorted(self, tmp_path):
        for ticket in ("90", "12"):
            (tmp_path / ticket).mkdir(parents=True)
            (tmp_path / ticket / "design-draft.md").write_text(
                "# d", encoding="utf-8"
            )
        (tmp_path / "12" / "tasks.md").write_text("# t", encoding="utf-8")
        drafts = fs.find_design_drafts(tmp_path)
        assert [Path(d).parent.name for d in drafts] == ["12", "90"]


def _draft(tmp_path: Path, ticket: str, depends_on: str = "") -> str:
    """Create task/{ticket}/design-draft.md and return its path string."""
    (tmp_path / ticket).mkdir(parents=True, exist_ok=True)
    fm = ['---', f'id: "design-{ticket}"', 'type: "design"']
    if depends_on:
        fm.append(f'depends-on: ["{depends_on}"]')
    fm += ['---', '# design', '']
    path = tmp_path / ticket / "design-draft.md"
    path.write_text("\n".join(fm), encoding="utf-8")
    return str(path)


class TestSelectDesignDrafts:
    def test_no_draft_is_scope_none(self):
        assert fs.select_design_drafts([]) == ([], [], "none")

    def test_ticket_argument_excludes_other_tickets(self, tmp_path):
        drafts = [_draft(tmp_path, "12"), _draft(tmp_path, "90")]
        selected, unscoped, scope = fs.select_design_drafts(drafts, "90")
        assert [Path(d).parent.name for d in selected] == ["90"]
        assert unscoped == []
        assert scope == "ticket"

    def test_unknown_ticket_selects_nothing(self, tmp_path):
        drafts = [_draft(tmp_path, "12"), _draft(tmp_path, "90")]
        assert fs.select_design_drafts(drafts, "77") == ([], [], "ticket")

    def test_depends_on_links_draft_to_target_spec(self, tmp_path):
        drafts = [
            _draft(tmp_path, "12", "spec-auth"),
            _draft(tmp_path, "90", "spec-billing"),
        ]
        selected, unscoped, scope = fs.select_design_drafts(
            drafts, "", {"spec-auth"}
        )
        assert [Path(d).parent.name for d in selected] == ["12"]
        assert unscoped == []
        assert scope == "depends-on"

    def test_single_draft_is_used_without_a_basis(self, tmp_path):
        drafts = [_draft(tmp_path, "12")]
        assert fs.select_design_drafts(drafts, "", {"spec-auth"}) == (
            drafts, [], "sole-draft",
        )

    def test_multiple_unlinked_drafts_are_left_unscoped(self, tmp_path):
        drafts = [_draft(tmp_path, "12"), _draft(tmp_path, "90")]
        selected, unscoped, scope = fs.select_design_drafts(
            drafts, "", {"spec-auth"}
        )
        assert selected == []
        assert unscoped == drafts
        assert scope == "unscoped"

    def test_single_draft_with_conflicting_depends_on_is_unscoped(self, tmp_path):
        # depends-on names a different spec entirely -- positive evidence the
        # draft belongs to another feature, unlike an untagged draft that
        # happens to be the only one on disk.
        drafts = [_draft(tmp_path, "12", "spec-billing")]
        selected, unscoped, scope = fs.select_design_drafts(
            drafts, "", {"spec-auth"}
        )
        assert selected == []
        assert unscoped == drafts
        assert scope == "unscoped"

    def test_conflicting_draft_is_excluded_leaving_untagged_sole_draft(self, tmp_path):
        conflicting = _draft(tmp_path, "12", "spec-billing")
        untagged = _draft(tmp_path, "90")
        selected, unscoped, scope = fs.select_design_drafts(
            [conflicting, untagged], "", {"spec-auth"}
        )
        assert selected == [untagged]
        assert unscoped == []
        assert scope == "sole-draft"


class TestSpecIdentifiers:
    def test_declared_and_derived_ids(self, tmp_path):
        (tmp_path / "auth").mkdir()
        flat = tmp_path / "billing_spec.md"
        flat.write_text('---\nid: "spec-billing-v2"\n---\n', encoding="utf-8")
        nested = tmp_path / "auth" / "user-login.md"
        nested.write_text("# no front matter\n", encoding="utf-8")

        ids = fs.spec_identifiers([str(flat), str(nested)], tmp_path)
        assert "spec-billing-v2" in ids     # declared front matter id
        assert "spec-billing" in ids        # derived from the file name
        assert "spec-user-login" in ids     # derived, suffix-free
        assert "spec-auth-user-login" in ids  # derived, hierarchical


class TestAdrCandidates:
    def test_both_naming_forms_at_the_specs_relative_location(self, tmp_path):
        spec_dir = tmp_path / "specification"
        adr_dir = tmp_path / "adr"
        spec = spec_dir / "auth" / "user-login_spec.md"

        names = [
            str(Path(c).relative_to(adr_dir)).replace(os.sep, "/")
            for c in fs.adr_candidates(adr_dir, spec, spec_dir)
        ]
        assert names == ["auth/user-login.md", "auth/user-login-decisions.md"]

    def test_flat_spec_maps_to_adr_root(self, tmp_path):
        spec_dir = tmp_path / "specification"
        adr_dir = tmp_path / "adr"
        names = [
            Path(c).name
            for c in fs.adr_candidates(adr_dir, spec_dir / "billing.md", spec_dir)
        ]
        assert names == ["billing.md", "billing-decisions.md"]


class TestSelectAdrDocs:
    def _dirs(self, tmp_path):
        spec_dir = tmp_path / "specification"
        adr_dir = tmp_path / "adr"
        spec_dir.mkdir()
        adr_dir.mkdir()
        return spec_dir, adr_dir

    def test_no_adr_directory_is_not_an_error(self, tmp_path):
        spec_dir = tmp_path / "specification"
        spec_dir.mkdir()
        spec = spec_dir / "auth.md"
        spec.write_text("# s", encoding="utf-8")
        assert fs.index_adr_docs(tmp_path / "adr") == {}
        assert fs.select_adr_docs(
            str(spec), spec_dir, tmp_path / "adr", {}
        ) == ([], "none")

    def test_name_match_covers_both_suffix_forms(self, tmp_path):
        spec_dir, adr_dir = self._dirs(tmp_path)
        spec = spec_dir / "auth_spec.md"
        spec.write_text("# s", encoding="utf-8")
        (adr_dir / "auth.md").write_text("# a", encoding="utf-8")
        (adr_dir / "auth-decisions.md").write_text("# a", encoding="utf-8")

        paths, basis = fs.select_adr_docs(
            str(spec), spec_dir, adr_dir, fs.index_adr_docs(adr_dir)
        )
        assert [Path(p).name for p in paths] == [
            "auth-decisions.md", "auth.md",
        ]
        assert basis == "name"

    def test_legacy_suffix_only_is_still_attributed(self, tmp_path):
        spec_dir, adr_dir = self._dirs(tmp_path)
        (spec_dir / "auth").mkdir()
        (adr_dir / "auth").mkdir()
        spec = spec_dir / "auth" / "user-login.md"
        spec.write_text("# s", encoding="utf-8")
        legacy = adr_dir / "auth" / "user-login-decisions.md"
        legacy.write_text("# a", encoding="utf-8")

        paths, basis = fs.select_adr_docs(
            str(spec), spec_dir, adr_dir, fs.index_adr_docs(adr_dir)
        )
        assert paths == [str(legacy)]
        assert basis == "name"

    def test_depends_on_fallback_when_the_name_differs(self, tmp_path):
        spec_dir, adr_dir = self._dirs(tmp_path)
        spec = spec_dir / "billing_spec.md"
        spec.write_text("# s", encoding="utf-8")
        renamed = adr_dir / "invoicing.md"
        renamed.write_text(
            '---\ndepends-on: ["spec-billing"]\n---\n# a', encoding="utf-8"
        )

        paths, basis = fs.select_adr_docs(
            str(spec), spec_dir, adr_dir, fs.index_adr_docs(adr_dir)
        )
        assert paths == [str(renamed)]
        assert basis == "depends-on"

    def test_unrelated_adr_is_not_attributed(self, tmp_path):
        spec_dir, adr_dir = self._dirs(tmp_path)
        spec = spec_dir / "billing.md"
        spec.write_text("# s", encoding="utf-8")
        (adr_dir / "auth.md").write_text(
            '---\ndepends-on: ["spec-auth"]\n---\n# a', encoding="utf-8"
        )

        assert fs.select_adr_docs(
            str(spec), spec_dir, adr_dir, fs.index_adr_docs(adr_dir)
        ) == ([], "none")


class TestParseArgs:
    def test_feature_only(self):
        assert fs.parse_args(["auth"]) == ("auth", "")

    def test_ticket_space_and_equals_forms(self):
        assert fs.parse_args(["auth", "--ticket", "90"]) == ("auth", "90")
        assert fs.parse_args(["--ticket=90", "auth"]) == ("auth", "90")

    def test_other_flags_are_not_mistaken_for_a_feature(self):
        assert fs.parse_args(["--full"]) == ("", "")
        assert fs.parse_args(["--full", "auth"]) == ("auth", "")

    def test_ticket_without_value_is_ignored(self):
        assert fs.parse_args(["auth", "--ticket"]) == ("auth", "")


# --- find-spec-docs.py E2E ------------------------------------------------

class TestFindSpecDocs:
    def test_custom_root_all_documents(self, proj_env):
        proj, env_file = proj_env
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "user-login_design.md").write_text("# d", encoding="utf-8")
        (spec_dir / "user-login_spec.md").write_text("# s", encoding="utf-8")
        result = _run(FIND_SPEC, proj, env_file)
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        assert (cache / "spec_files.txt").is_file()
        assert (cache / "design_draft_files.txt").is_file()
        assert (cache / "file_mapping.json").is_file()
        # bare .sdd/ を作らない
        assert not (proj / ".sdd").exists()

        spec_txt = (cache / "spec_files.txt").read_text(encoding="utf-8")
        assert "user-login_spec.md" in spec_txt
        # 永続 design doc は spec 一覧に混ぜない
        assert "user-login_design.md" not in spec_txt

        mapping = json.loads((cache / "file_mapping.json").read_text(encoding="utf-8"))
        assert mapping["spec_documents"][0]["feature_name"] == "user-login"
        assert mapping["spec_documents"][0]["spec"].endswith("user-login_spec.md")
        assert mapping["spec_documents"][0]["design"].endswith(
            "user-login_design.md"
        )
        assert mapping["design_drafts"] == []

        env = env_file.read_text(encoding="utf-8")
        assert "CHECK_SPEC_CACHE_DIR" in env
        assert "CHECK_SPEC_SPEC_FILES" in env
        assert "CHECK_SPEC_DESIGN_DRAFT_FILES" in env
        assert f"{ROOT}/.cache/check-spec" in env

    def test_specs_listed_without_any_design_doc(self, proj_env):
        # v5.0.0: design docs no longer live under specification/, so a spec-only
        # tree must still produce a spec list (and no warning-driven failure).
        proj, env_file = proj_env
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "user-login_spec.md").write_text("# s", encoding="utf-8")
        (spec_dir / "billing.md").write_text("# s", encoding="utf-8")
        result = _run(FIND_SPEC, proj, env_file)
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        spec_lines = (cache / "spec_files.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        assert len(spec_lines) == 2
        assert any(line.endswith("billing.md") for line in spec_lines)
        assert any(line.endswith("user-login_spec.md") for line in spec_lines)

        mapping = json.loads((cache / "file_mapping.json").read_text(encoding="utf-8"))
        assert [d["feature_name"] for d in mapping["spec_documents"]] == [
            "billing", "user-login",
        ]
        assert all(d["design"] == "" for d in mapping["spec_documents"])
        assert "WARNING" not in result.stderr

    def test_suffixless_and_suffixed_specs_both_detected(self, proj_env):
        proj, env_file = proj_env
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "auth.md").write_text("# s", encoding="utf-8")
        (spec_dir / "auth_spec.md").write_text("# s", encoding="utf-8")
        result = _run(FIND_SPEC, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        spec_txt = (cache / "spec_files.txt").read_text(encoding="utf-8")
        assert "auth.md" in spec_txt
        assert "auth_spec.md" in spec_txt

    def test_design_draft_is_optional_auxiliary_input(self, proj_env):
        proj, env_file = proj_env
        (proj / ROOT / "specification" / "auth_spec.md").write_text(
            "# s", encoding="utf-8"
        )
        draft_dir = proj / ROOT / "task" / "90"
        draft_dir.mkdir(parents=True)
        (draft_dir / "design-draft.md").write_text("# d", encoding="utf-8")
        result = _run(FIND_SPEC, proj, env_file)
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        drafts_txt = (cache / "design_draft_files.txt").read_text(encoding="utf-8")
        assert "task/90/design-draft.md" in drafts_txt.replace(os.sep, "/")

        mapping = json.loads((cache / "file_mapping.json").read_text(encoding="utf-8"))
        assert len(mapping["design_drafts"]) == 1
        assert mapping["design_drafts"][0].endswith("design-draft.md")
        assert mapping["design_draft_scope"] == "sole-draft"
        assert mapping["unscoped_design_drafts"] == []

    def test_ticket_option_scopes_the_design_draft(self, proj_env):
        # Parallel tickets: only the requested ticket's draft may be attached.
        proj, env_file = proj_env
        (proj / ROOT / "specification" / "auth_spec.md").write_text(
            "# s", encoding="utf-8"
        )
        task_dir = proj / ROOT / "task"
        _draft(task_dir, "12")
        _draft(task_dir, "90")

        for args in (("--ticket", "90"), ("--ticket=90",)):
            result = _run(FIND_SPEC, proj, env_file, *args)
            assert result.returncode == 0, result.stderr

            cache = proj / ROOT / ".cache" / "check-spec"
            mapping = json.loads(
                (cache / "file_mapping.json").read_text(encoding="utf-8")
            )
            assert mapping["design_draft_scope"] == "ticket"
            assert [
                Path(d).parent.name for d in mapping["design_drafts"]
            ] == ["90"]

            drafts_txt = (cache / "design_draft_files.txt").read_text(
                encoding="utf-8"
            ).replace(os.sep, "/")
            assert "task/90/design-draft.md" in drafts_txt
            assert "task/12/design-draft.md" not in drafts_txt
            assert 'CHECK_SPEC_DESIGN_DRAFT_SCOPE="ticket"' in env_file.read_text(
                encoding="utf-8"
            )

    def test_depends_on_scopes_the_design_draft(self, proj_env):
        proj, env_file = proj_env
        (proj / ROOT / "specification" / "auth_spec.md").write_text(
            '---\nid: "spec-auth"\n---\n# s', encoding="utf-8"
        )
        (proj / ROOT / "specification" / "billing.md").write_text(
            '---\nid: "spec-billing"\n---\n# s', encoding="utf-8"
        )
        task_dir = proj / ROOT / "task"
        _draft(task_dir, "12", "spec-auth")
        _draft(task_dir, "90", "spec-billing")

        result = _run(FIND_SPEC, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        mapping = json.loads(
            (cache / "file_mapping.json").read_text(encoding="utf-8")
        )
        assert mapping["design_draft_scope"] == "depends-on"
        assert [
            Path(d).parent.name for d in mapping["design_drafts"]
        ] == ["12"]

    def test_unscoped_drafts_are_reported_not_attached(self, proj_env):
        proj, env_file = proj_env
        (proj / ROOT / "specification" / "auth_spec.md").write_text(
            "# s", encoding="utf-8"
        )
        task_dir = proj / ROOT / "task"
        _draft(task_dir, "12")
        _draft(task_dir, "90")

        result = _run(FIND_SPEC, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr
        assert "WARNING" in result.stderr
        assert "--ticket" in result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        assert (cache / "design_draft_files.txt").read_text(
            encoding="utf-8"
        ) == ""
        mapping = json.loads(
            (cache / "file_mapping.json").read_text(encoding="utf-8")
        )
        assert mapping["design_drafts"] == []
        assert mapping["design_draft_scope"] == "unscoped"
        assert len(mapping["unscoped_design_drafts"]) == 2

    def test_adr_is_resolved_under_the_custom_root(self, proj_env):
        # /check-spec --full needs the feature's decision log as input for the
        # spec <-> adr document review.
        proj, env_file = proj_env
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "auth").mkdir()
        (spec_dir / "auth" / "user-login.md").write_text("# s", encoding="utf-8")
        adr_dir = proj / ROOT / "adr" / "auth"
        adr_dir.mkdir(parents=True)
        # legacy `-decisions` suffix stays valid on existing files
        (adr_dir / "user-login-decisions.md").write_text("# a", encoding="utf-8")

        result = _run(FIND_SPEC, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr
        assert "WARNING" not in result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        adr_txt = (cache / "adr_files.txt").read_text(
            encoding="utf-8"
        ).replace(os.sep, "/")
        assert "adr/auth/user-login-decisions.md" in adr_txt

        mapping = json.loads(
            (cache / "file_mapping.json").read_text(encoding="utf-8")
        )
        entry = mapping["spec_documents"][0]
        assert [Path(p).name for p in entry["adr"]] == [
            "user-login-decisions.md",
        ]
        assert entry["adr_basis"] == "name"
        assert len(mapping["adr_documents"]) == 1

        env = env_file.read_text(encoding="utf-8")
        assert "CHECK_SPEC_ADR_FILES" in env
        assert f"{ROOT}/.cache/check-spec/adr_files.txt" in env.replace(
            os.sep, "/"
        )

    def test_missing_adr_is_normal_not_an_error(self, proj_env):
        proj, env_file = proj_env
        (proj / ROOT / "specification" / "auth_spec.md").write_text(
            "# s", encoding="utf-8"
        )

        result = _run(FIND_SPEC, proj, env_file)
        assert result.returncode == 0, result.stderr
        assert "WARNING" not in result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        assert (cache / "adr_files.txt").read_text(encoding="utf-8") == ""
        mapping = json.loads(
            (cache / "file_mapping.json").read_text(encoding="utf-8")
        )
        assert mapping["adr_documents"] == []
        assert mapping["spec_documents"][0]["adr"] == []
        assert mapping["spec_documents"][0]["adr_basis"] == "none"

    def test_custom_adr_directory_name_is_honored(self, tmp_path):
        proj = _make_project(tmp_path)
        config = json.loads(
            (proj / ".sdd-config.json").read_text(encoding="utf-8")
        )
        config["directories"]["adr"] = "decisions"
        (proj / ".sdd-config.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        (proj / ROOT / "specification" / "auth.md").write_text(
            "# s", encoding="utf-8"
        )
        (proj / ROOT / "decisions").mkdir(parents=True)
        (proj / ROOT / "decisions" / "auth.md").write_text(
            "# a", encoding="utf-8"
        )
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")

        result = _run(FIND_SPEC, proj, env_file)
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        adr_txt = (cache / "adr_files.txt").read_text(
            encoding="utf-8"
        ).replace(os.sep, "/")
        assert f"{ROOT}/decisions/auth.md" in adr_txt

    def test_flag_only_argument_targets_all_specs(self, proj_env):
        # `/check-spec --full` must not treat "--full" as a feature name.
        proj, env_file = proj_env
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "auth_spec.md").write_text("# s", encoding="utf-8")
        (spec_dir / "billing.md").write_text("# s", encoding="utf-8")

        result = _run(FIND_SPEC, proj, env_file, "--full")
        assert result.returncode == 0, result.stderr
        assert "WARNING" not in result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        spec_lines = (cache / "spec_files.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        assert len(spec_lines) == 2

    def test_feature_flat_structure(self, proj_env):
        proj, env_file = proj_env
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "auth_spec.md").write_text("# s", encoding="utf-8")
        (spec_dir / "other_spec.md").write_text("# s", encoding="utf-8")
        result = _run(FIND_SPEC, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        spec_txt = (cache / "spec_files.txt").read_text(encoding="utf-8")
        assert "auth_spec.md" in spec_txt
        assert "other_spec.md" not in spec_txt

    def test_feature_hierarchical_structure(self, proj_env):
        proj, env_file = proj_env
        feature_dir = proj / ROOT / "specification" / "auth"
        feature_dir.mkdir()
        (feature_dir / "index_spec.md").write_text("# s", encoding="utf-8")
        (feature_dir / "user-login.md").write_text("# s", encoding="utf-8")
        result = _run(FIND_SPEC, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        spec_txt = (cache / "spec_files.txt").read_text(
            encoding="utf-8"
        ).replace(os.sep, "/")
        assert "auth/index_spec.md" in spec_txt
        assert "auth/user-login.md" in spec_txt

    def test_missing_specification_dir_exits_nonzero(self, tmp_path):
        proj = tmp_path / "project"
        proj.mkdir()
        config = {"root": ROOT, "lang": "en"}
        (proj / ".sdd-config.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")
        result = _run(FIND_SPEC, proj, env_file)
        assert result.returncode != 0

    def test_env_export_replaces_existing_vars(self, proj_env):
        proj, env_file = proj_env
        (proj / ROOT / "specification" / "x_spec.md").write_text(
            "# s", encoding="utf-8"
        )
        env_file.write_text(
            'export CHECK_SPEC_CACHE_DIR="stale"\nexport OTHER="keep"\n',
            encoding="utf-8",
        )

        result = _run(FIND_SPEC, proj, env_file)
        assert result.returncode == 0, result.stderr

        env = env_file.read_text(encoding="utf-8")
        assert 'export OTHER="keep"' in env
        assert "stale" not in env
        assert env.count("export CHECK_SPEC_CACHE_DIR=") == 1


# --- validate-files.py E2E ------------------------------------------------

class TestValidateFiles:
    def test_custom_root_scan(self, tmp_path):
        proj = _make_project(tmp_path)
        (proj / ROOT / "requirement" / "user-login.md").write_text(
            "# prd", encoding="utf-8"
        )
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "user-login_spec.md").write_text("# s", encoding="utf-8")
        (spec_dir / "user-logout.md").write_text("# s", encoding="utf-8")
        (spec_dir / "user-login_design.md").write_text("# d", encoding="utf-8")
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")

        result = _run(VALIDATE_FILES, proj, env_file)
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "constitution"
        assert (cache / "requirement_files.txt").is_file()
        assert (cache / "spec_files.txt").is_file()
        assert (cache / "design_files.txt").is_file()
        assert (cache / "scan_summary.json").is_file()
        assert not (proj / ".sdd").exists()

        summary = json.loads(
            (cache / "scan_summary.json").read_text(encoding="utf-8")
        )
        assert summary["requirement_files"] == 1
        # The `_spec` suffix is optional, so both forms count as specs and the
        # v4.x design doc is not double-counted among them.
        assert summary["spec_files"] == 2
        assert summary["design_files"] == 1
        assert summary["total_files"] == 4
        assert summary["scanned_at"].endswith("Z")

        spec_txt = (cache / "spec_files.txt").read_text(encoding="utf-8")
        assert "user-login_spec.md" in spec_txt
        assert "user-logout.md" in spec_txt
        assert "user-login_design.md" not in spec_txt

        env = env_file.read_text(encoding="utf-8")
        assert "CONSTITUTION_CACHE_DIR" in env
        assert f"{ROOT}/.cache/constitution" in env

    def test_missing_dirs_zero_counts(self, tmp_path):
        proj = tmp_path / "project"
        proj.mkdir()
        config = {"root": ROOT, "lang": "en"}
        (proj / ".sdd-config.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")

        result = _run(VALIDATE_FILES, proj, env_file)
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "constitution"
        summary = json.loads(
            (cache / "scan_summary.json").read_text(encoding="utf-8")
        )
        assert summary["total_files"] == 0
