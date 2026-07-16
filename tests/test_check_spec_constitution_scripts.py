"""check-spec / constitution のヘルパースクリプトのユニットテスト（pytest）。

scripts/test-skill-scripts.sh の custom-root 回帰テストを補完し、
find-design-docs.py / validate-files.py の関数単位・E2E 挙動を検証する:
  - custom root 配下への .cache 生成
  - フラット / 階層 / 部分一致でのデザイン文書検出
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
FIND_DESIGN = (
    PLUGIN_ROOT / "skills" / "check-spec" / "scripts" / "find-design-docs.py"
)
VALIDATE_FILES = (
    PLUGIN_ROOT / "skills" / "constitution" / "scripts" / "validate-files.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fd = _load_module("find_design_docs", FIND_DESIGN)
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
        cfg = fd.read_config(tmp_path)
        assert cfg == {
            "root": ".sdd",
            "requirement": "requirement",
            "specification": "specification",
        }

    def test_missing_config_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            fd.read_config(tmp_path)


class TestSortedMatches:
    def test_recursive_and_sorted(self, tmp_path):
        (tmp_path / "b").mkdir()
        (tmp_path / "b" / "z_design.md").write_text("", encoding="utf-8")
        (tmp_path / "a_design.md").write_text("", encoding="utf-8")
        (tmp_path / "note_spec.md").write_text("", encoding="utf-8")
        result = fd.sorted_matches(tmp_path, "*_design.md")
        assert result == sorted(result)
        assert len(result) == 2
        assert all(p.endswith("_design.md") for p in result)


# --- find-design-docs.py E2E ----------------------------------------------

class TestFindDesignDocs:
    def test_custom_root_all_documents(self, tmp_path):
        proj = _make_project(tmp_path)
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "user-login_design.md").write_text("# d", encoding="utf-8")
        (spec_dir / "user-login_spec.md").write_text("# s", encoding="utf-8")
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")

        result = _run(FIND_DESIGN, proj, env_file)
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        assert (cache / "design_files.txt").is_file()
        assert (cache / "spec_files.txt").is_file()
        assert (cache / "file_mapping.json").is_file()
        # bare .sdd/ を作らない
        assert not (proj / ".sdd").exists()

        design_txt = (cache / "design_files.txt").read_text(encoding="utf-8")
        assert "user-login_design.md" in design_txt

        mapping = json.loads((cache / "file_mapping.json").read_text(encoding="utf-8"))
        assert mapping["design_documents"][0]["feature_name"] == "user-login"
        assert mapping["design_documents"][0]["spec"].endswith(
            "user-login_spec.md"
        )

        env = env_file.read_text(encoding="utf-8")
        assert "CHECK_SPEC_CACHE_DIR" in env
        assert f"{ROOT}/.cache/check-spec" in env

    def test_feature_flat_structure(self, tmp_path):
        proj = _make_project(tmp_path)
        spec_dir = proj / ROOT / "specification"
        (spec_dir / "auth_design.md").write_text("# d", encoding="utf-8")
        (spec_dir / "auth_spec.md").write_text("# s", encoding="utf-8")
        (spec_dir / "other_design.md").write_text("# d", encoding="utf-8")
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")

        result = _run(FIND_DESIGN, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        design_txt = (cache / "design_files.txt").read_text(encoding="utf-8")
        assert "auth_design.md" in design_txt
        assert "other_design.md" not in design_txt

    def test_feature_hierarchical_structure(self, tmp_path):
        proj = _make_project(tmp_path)
        feature_dir = proj / ROOT / "specification" / "auth"
        feature_dir.mkdir()
        (feature_dir / "index_design.md").write_text("# d", encoding="utf-8")
        (feature_dir / "index_spec.md").write_text("# s", encoding="utf-8")
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")

        result = _run(FIND_DESIGN, proj, env_file, "auth")
        assert result.returncode == 0, result.stderr

        cache = proj / ROOT / ".cache" / "check-spec"
        design_txt = (cache / "design_files.txt").read_text(encoding="utf-8")
        assert "auth/index_design.md" in design_txt

    def test_missing_specification_dir_exits_nonzero(self, tmp_path):
        proj = tmp_path / "project"
        proj.mkdir()
        config = {"root": ROOT, "lang": "en"}
        (proj / ".sdd-config.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")

        result = _run(FIND_DESIGN, proj, env_file)
        assert result.returncode != 0

    def test_env_export_replaces_existing_vars(self, tmp_path):
        proj = _make_project(tmp_path)
        (proj / ROOT / "specification" / "x_design.md").write_text(
            "# d", encoding="utf-8"
        )
        env_file = tmp_path / "env"
        env_file.write_text(
            'export CHECK_SPEC_CACHE_DIR="stale"\nexport OTHER="keep"\n',
            encoding="utf-8",
        )

        result = _run(FIND_DESIGN, proj, env_file)
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
