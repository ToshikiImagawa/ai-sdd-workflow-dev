"""scan-documents.py のユニットテスト（pytest）。

Front Matter 検出、ドキュメント種別判定、タイトル抽出、
custom root 配下の .cache 生成、CLAUDE_ENV_FILE エクスポートを検証する。
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
    / "recommend-front-matter"
    / "scripts"
    / "scan-documents.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("scan_documents", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sd = _load_module()


# --- has_front_matter ------------------------------------------------------


class TestHasFrontMatter:
    def test_with_front_matter(self):
        lines = ["---", "id: x", "title: T", "---", "# Body"]
        has_fm, closing = sd.has_front_matter(lines)
        assert has_fm is True
        assert closing == 3

    def test_without_front_matter(self):
        lines = ["# Just a heading", "body"]
        has_fm, closing = sd.has_front_matter(lines)
        assert has_fm is False
        assert closing == 0

    def test_unclosed_front_matter(self):
        lines = ["---", "id: x", "no closing"]
        has_fm, _ = sd.has_front_matter(lines)
        assert has_fm is False

    def test_closing_beyond_50_lines(self):
        lines = ["---"] + [f"key{i}: v" for i in range(60)] + ["---"]
        has_fm, _ = sd.has_front_matter(lines)
        assert has_fm is False

    def test_empty_file(self):
        assert sd.has_front_matter([]) == (False, 0)


# --- determine_type --------------------------------------------------------


class TestDetermineType:
    def test_requirement_is_prd(self):
        assert (
            sd.determine_type(
                "/p/.sdd/requirement/login.md", "login",
                "requirement", "specification", "task",
            )
            == "prd"
        )

    def test_specification_spec(self):
        assert (
            sd.determine_type(
                "/p/.sdd/specification/login_spec.md", "login_spec",
                "requirement", "specification", "task",
            )
            == "spec"
        )

    def test_specification_design(self):
        assert (
            sd.determine_type(
                "/p/.sdd/specification/login_design.md", "login_design",
                "requirement", "specification", "task",
            )
            == "design"
        )

    def test_specification_unknown(self):
        assert (
            sd.determine_type(
                "/p/.sdd/specification/notes.md", "notes",
                "requirement", "specification", "task",
            )
            == "unknown"
        )

    def test_task_implementation_log(self):
        assert (
            sd.determine_type(
                "/p/.sdd/task/impl_log.md", "impl_log",
                "requirement", "specification", "task",
            )
            == "implementation-log"
        )

    def test_task_plain(self):
        assert (
            sd.determine_type(
                "/p/.sdd/task/notes.md", "notes",
                "requirement", "specification", "task",
            )
            == "task"
        )

    def test_outside_known_dirs(self):
        assert (
            sd.determine_type(
                "/p/.sdd/other/x.md", "x",
                "requirement", "specification", "task",
            )
            == "unknown"
        )


# --- extract_title ---------------------------------------------------------


class TestExtractTitle:
    def test_heading_after_front_matter(self):
        lines = ["---", "id: x", "---", "# Real Title", "body"]
        assert sd.extract_title(lines, "fallback") == "Real Title"

    def test_heading_without_front_matter(self):
        lines = ["# Only Heading", "body"]
        assert sd.extract_title(lines, "fallback") == "Only Heading"

    def test_h2_is_ignored(self):
        lines = ["## Subheading", "body"]
        assert sd.extract_title(lines, "fallback") == "fallback"

    def test_no_heading_falls_back_to_basename(self):
        lines = ["just text", "more text"]
        assert sd.extract_title(lines, "my-doc") == "my-doc"

    def test_empty_heading_falls_back(self):
        lines = ["# ", "body"]
        assert sd.extract_title(lines, "my-doc") == "my-doc"


# --- read_config -----------------------------------------------------------


class TestReadConfig:
    def test_defaults_when_fields_missing(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text("{}", encoding="utf-8")
        config = sd.read_config(tmp_path)
        assert config == {
            "root": ".sdd",
            "requirement": "requirement",
            "specification": "specification",
            "task": "task",
            "lang": "en",
        }

    def test_custom_values(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text(
            json.dumps(
                {
                    "root": ".ai",
                    "lang": "ja",
                    "directories": {
                        "requirement": "req",
                        "specification": "spec",
                        "task": "tasks",
                    },
                }
            ),
            encoding="utf-8",
        )
        config = sd.read_config(tmp_path)
        assert config["root"] == ".ai"
        assert config["lang"] == "ja"
        assert config["requirement"] == "req"
        assert config["specification"] == "spec"
        assert config["task"] == "tasks"

    def test_missing_config_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            sd.read_config(tmp_path)


# --- collect_documents -----------------------------------------------------


class TestCollectDocuments:
    def _config(self):
        return {
            "root": ".sdd",
            "requirement": "requirement",
            "specification": "specification",
            "task": "task",
            "lang": "en",
        }

    def test_specification_filters_by_suffix(self, tmp_path):
        sdd_dir = tmp_path / ".sdd"
        (sdd_dir / "specification").mkdir(parents=True)
        (sdd_dir / "specification" / "a_spec.md").write_text("# a", encoding="utf-8")
        (sdd_dir / "specification" / "a_design.md").write_text("# a", encoding="utf-8")
        (sdd_dir / "specification" / "notes.md").write_text("# n", encoding="utf-8")

        docs = sd.collect_documents(
            sdd_dir, "requirement", "specification", "task",
        )
        names = sorted(p.name for p in docs)
        assert names == ["a_design.md", "a_spec.md"]

    def test_requirement_and_task_include_all_md(self, tmp_path):
        sdd_dir = tmp_path / ".sdd"
        (sdd_dir / "requirement" / "nested").mkdir(parents=True)
        (sdd_dir / "task").mkdir(parents=True)
        (sdd_dir / "requirement" / "index.md").write_text("# i", encoding="utf-8")
        (sdd_dir / "requirement" / "nested" / "child.md").write_text(
            "# c", encoding="utf-8"
        )
        (sdd_dir / "task" / "log.md").write_text("# l", encoding="utf-8")

        docs = sd.collect_documents(
            sdd_dir, "requirement", "specification", "task",
        )
        names = sorted(p.name for p in docs)
        assert names == ["child.md", "index.md", "log.md"]


# --- end to end ------------------------------------------------------------


class TestEndToEnd:
    def _run(self, monkeypatch, project_root, env_file):
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_root))
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
        sd.main()

    def test_custom_root_scan(self, tmp_path, monkeypatch):
        root = ".ai-docs"
        proj = tmp_path / "project"
        for sub in ("requirement", "specification", "task"):
            (proj / root / sub).mkdir(parents=True)
        (proj / ".sdd-config.json").write_text(
            json.dumps(
                {
                    "root": root,
                    "lang": "ja",
                    "directories": {
                        "requirement": "requirement",
                        "specification": "specification",
                        "task": "task",
                    },
                }
            ),
            encoding="utf-8",
        )
        (proj / root / "requirement" / "login.md").write_text(
            "---\nid: x\n---\n# Login PRD\n", encoding="utf-8"
        )
        (proj / root / "specification" / "login_spec.md").write_text(
            "# Login Spec\n", encoding="utf-8"
        )
        (proj / root / "specification" / "notes.md").write_text(
            "# ignored\n", encoding="utf-8"
        )

        env_file = tmp_path / "env_output"
        env_file.write_text("", encoding="utf-8")
        self._run(monkeypatch, proj, env_file)

        cache = proj / root / ".cache" / "recommend-front-matter"
        scan_result = cache / "scan_result.json"
        assert scan_result.is_file()
        # No bare .sdd/ directory is created under a custom root.
        assert not (proj / ".sdd").exists()

        data = json.loads(scan_result.read_text(encoding="utf-8"))
        assert data["total_documents"] == 2
        assert data["documents_with_front_matter"] == 1
        assert data["documents_without_front_matter"] == 1

        by_name = {d["basename"]: d for d in data["documents"]}
        assert by_name["login"]["type"] == "prd"
        assert by_name["login"]["has_front_matter"] is True
        assert by_name["login"]["title_line"] == "Login PRD"
        assert by_name["login_spec"]["type"] == "spec"
        assert by_name["login_spec"]["has_front_matter"] is False
        assert "notes" not in by_name

        env_contents = env_file.read_text(encoding="utf-8")
        assert "RECOMMEND_FM_CACHE_DIR" in env_contents
        assert f"{root}/.cache/recommend-front-matter" in env_contents
        assert "RECOMMEND_FM_SCAN_RESULT" in env_contents
        assert 'export SDD_LANG="ja"' in env_contents

    def test_env_file_dedup_removes_stale_vars(self, tmp_path, monkeypatch):
        proj = tmp_path / "project"
        (proj / ".sdd" / "requirement").mkdir(parents=True)
        (proj / ".sdd-config.json").write_text("{}", encoding="utf-8")
        (proj / ".sdd" / "requirement" / "a.md").write_text("# A", encoding="utf-8")

        env_file = tmp_path / "env_output"
        env_file.write_text(
            'export RECOMMEND_FM_CACHE_DIR="/stale"\n'
            'export OTHER_VAR="keep"\n',
            encoding="utf-8",
        )
        self._run(monkeypatch, proj, env_file)

        env_contents = env_file.read_text(encoding="utf-8")
        assert "/stale" not in env_contents
        assert 'export OTHER_VAR="keep"' in env_contents
        assert env_contents.count("RECOMMEND_FM_CACHE_DIR") == 1
