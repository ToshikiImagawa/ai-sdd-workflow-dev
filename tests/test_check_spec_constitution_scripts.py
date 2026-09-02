"""check-spec / constitution のヘルパースクリプトのユニットテスト（pytest）。

scripts/test-skill-scripts.sh の custom-root 回帰テストを補完し、
find-spec-docs.py / validate-files.py の関数単位・E2E 挙動を検証する:
  - custom root 配下への .cache 生成
  - フラット / 階層 / 部分一致での spec 文書検出（サフィックス有無の両方）
  - design doc が 0 件でも spec 一覧が出力されること
  - design draft の任意入力としての取り込み
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

    def test_missing_config_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            fs.read_config(tmp_path)


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
        assert summary["spec_files"] == 1
        assert summary["design_files"] == 1
        assert summary["total_files"] == 3
        assert summary["scanned_at"].endswith("Z")

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
