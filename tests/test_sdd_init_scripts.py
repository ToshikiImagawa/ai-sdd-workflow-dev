"""sdd-init ヘルパースクリプト（init-structure.py / update-claude-md.py）のユニットテスト。

通しE2E（scripts/test-e2e-sdd-init.sh）を補完し、関数単位のエッジケース
（設定欠如・デフォルト補完・env エクスポート・セクション置換・バージョン抽出等）を検証する。
"""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "skills" / "sdd-init" / "scripts"
)


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


init_structure = _load_module("init_structure", "init-structure.py")
update_claude_md = _load_module("update_claude_md", "update-claude-md.py")


# ---------------------------------------------------------------------------
# init-structure.py
# ---------------------------------------------------------------------------
class TestReadConfig:
    def test_missing_config_exits(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            init_structure.read_config(tmp_path / ".sdd-config.json")
        assert exc.value.code == 1

    def test_defaults_when_fields_absent(self, tmp_path):
        config_path = tmp_path / ".sdd-config.json"
        config_path.write_text("{}", encoding="utf-8")

        result = init_structure.read_config(config_path)
        assert result == {
            "root": ".sdd",
            "requirement": "requirement",
            "specification": "specification",
            "task": "task",
            "lang": "en",
        }

    def test_custom_values_are_honored(self, tmp_path):
        config_path = tmp_path / ".sdd-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "root": ".ai-docs",
                    "lang": "ja",
                    "directories": {
                        "requirement": "reqs",
                        "specification": "specs",
                        "task": "tasks",
                    },
                }
            ),
            encoding="utf-8",
        )

        result = init_structure.read_config(config_path)
        assert result == {
            "root": ".ai-docs",
            "requirement": "reqs",
            "specification": "specs",
            "task": "tasks",
            "lang": "ja",
        }

    def test_null_directories_fall_back_to_defaults(self, tmp_path):
        config_path = tmp_path / ".sdd-config.json"
        config_path.write_text(
            json.dumps({"root": ".sdd", "directories": None}), encoding="utf-8"
        )
        result = init_structure.read_config(config_path)
        assert result["requirement"] == "requirement"


class TestCopyTemplates:
    def _make_plugin(self, plugin_root: Path, lang: str = "en") -> None:
        for skill, name in (
            ("generate-prd", "prd_template.md"),
            ("generate-spec", "spec_template.md"),
            ("generate-spec", "design_template.md"),
        ):
            src = plugin_root / "skills" / skill / "templates" / lang / name
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text(f"source:{name}", encoding="utf-8")

    def test_copies_missing_templates(self, tmp_path, capsys):
        plugin_root = tmp_path / "plugin"
        self._make_plugin(plugin_root)
        sdd_dir = tmp_path / ".sdd"
        sdd_dir.mkdir()

        init_structure.copy_templates(sdd_dir, plugin_root, "en")

        assert (sdd_dir / "PRD_TEMPLATE.md").read_text(encoding="utf-8") == "source:prd_template.md"
        assert (sdd_dir / "SPECIFICATION_TEMPLATE.md").is_file()
        assert (sdd_dir / "DESIGN_DOC_TEMPLATE.md").is_file()
        assert "Templates copied: 3, skipped: 0" in capsys.readouterr().err

    def test_existing_templates_are_not_overwritten(self, tmp_path, capsys):
        plugin_root = tmp_path / "plugin"
        self._make_plugin(plugin_root)
        sdd_dir = tmp_path / ".sdd"
        sdd_dir.mkdir()
        (sdd_dir / "PRD_TEMPLATE.md").write_text("customized", encoding="utf-8")

        init_structure.copy_templates(sdd_dir, plugin_root, "en")

        assert (sdd_dir / "PRD_TEMPLATE.md").read_text(encoding="utf-8") == "customized"
        assert "Templates copied: 2, skipped: 1" in capsys.readouterr().err

    def test_missing_source_warns(self, tmp_path, capsys):
        plugin_root = tmp_path / "plugin"  # no templates created
        sdd_dir = tmp_path / ".sdd"
        sdd_dir.mkdir()

        init_structure.copy_templates(sdd_dir, plugin_root, "en")

        err = capsys.readouterr().err
        assert "Templates copied: 0, skipped: 0" in err
        assert "WARNING: Source template not found" in err


class TestExportEnvVars:
    def test_writes_all_sdd_vars(self, tmp_path, monkeypatch):
        env_file = tmp_path / "env"
        env_file.write_text("", encoding="utf-8")
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))

        config = {
            "root": ".ai-docs",
            "requirement": "reqs",
            "specification": "specs",
            "task": "tasks",
            "lang": "ja",
        }
        init_structure.export_env_vars(config)

        content = env_file.read_text(encoding="utf-8")
        assert 'export SDD_ROOT=".ai-docs"' in content
        assert 'export SDD_REQUIREMENT_DIR="reqs"' in content
        assert 'export SDD_REQUIREMENT_PATH=".ai-docs/reqs"' in content
        assert 'export SDD_SPECIFICATION_PATH=".ai-docs/specs"' in content
        assert 'export SDD_TASK_PATH=".ai-docs/tasks"' in content
        assert 'export SDD_LANG="ja"' in content

    def test_removes_existing_sdd_vars(self, tmp_path, monkeypatch):
        env_file = tmp_path / "env"
        env_file.write_text(
            'export SDD_ROOT="stale"\nexport OTHER="keep"\n', encoding="utf-8"
        )
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))

        config = {
            "root": ".sdd",
            "requirement": "requirement",
            "specification": "specification",
            "task": "task",
            "lang": "en",
        }
        init_structure.export_env_vars(config)

        content = env_file.read_text(encoding="utf-8")
        assert 'export OTHER="keep"' in content
        assert content.count('export SDD_ROOT=') == 1
        assert 'export SDD_ROOT="stale"' not in content

    def test_noop_without_env_file(self, monkeypatch):
        monkeypatch.delenv("CLAUDE_ENV_FILE", raising=False)
        # 例外を投げず、何もしないこと
        init_structure.export_env_vars(
            {
                "root": ".sdd",
                "requirement": "requirement",
                "specification": "specification",
                "task": "task",
                "lang": "en",
            }
        )


# ---------------------------------------------------------------------------
# update-claude-md.py
# ---------------------------------------------------------------------------
class TestResolveLangAndRoot:
    def test_config_takes_priority_over_env(self, tmp_path, monkeypatch):
        (tmp_path / ".sdd-config.json").write_text(
            json.dumps({"lang": "ja", "root": ".ai-docs"}), encoding="utf-8"
        )
        monkeypatch.setenv("SDD_LANG", "en")
        monkeypatch.setenv("SDD_ROOT", ".sdd")

        lang, root = update_claude_md.resolve_lang_and_root(tmp_path)
        assert lang == "ja"
        assert root == ".ai-docs"

    def test_env_fallback_when_no_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SDD_LANG", "ja")
        monkeypatch.delenv("SDD_ROOT", raising=False)

        lang, root = update_claude_md.resolve_lang_and_root(tmp_path)
        assert lang == "ja"
        assert root == ".sdd"

    def test_defaults_when_config_invalid(self, tmp_path, monkeypatch):
        (tmp_path / ".sdd-config.json").write_text("{ broken", encoding="utf-8")
        monkeypatch.delenv("SDD_LANG", raising=False)
        monkeypatch.delenv("SDD_ROOT", raising=False)

        lang, root = update_claude_md.resolve_lang_and_root(tmp_path)
        assert lang == "en"
        assert root == ".sdd"


class TestExtractCurrentVersion:
    def test_extracts_version_from_title(self):
        md = "# Title\n\n## AI-SDD Instructions (v3.3.0)\n\nbody\n"
        assert update_claude_md.extract_current_version(md) == "3.3.0"

    def test_no_section_returns_unknown(self):
        assert update_claude_md.extract_current_version("# Title\n") == "unknown"

    def test_section_without_version_returns_unknown(self):
        md = "## AI-SDD Instructions\n"
        assert update_claude_md.extract_current_version(md) == "unknown"

    def test_uses_first_matching_line(self):
        md = "## AI-SDD Instructions (v1.0.0)\n## AI-SDD Instructions (v2.0.0)\n"
        assert update_claude_md.extract_current_version(md) == "1.0.0"


class TestReplaceSection:
    def test_replaces_only_the_section(self):
        existing = (
            "# Project\n\n"
            "## AI-SDD Instructions (v1.0.0)\n\n"
            "old body line\n\n"
            "## Other Section\n\n"
            "keep me\n"
        )
        new = "## AI-SDD Instructions (v2.0.0)\n\nnew body\n"
        result = update_claude_md.replace_section(existing, new)

        assert "## AI-SDD Instructions (v2.0.0)" in result
        assert "new body" in result
        assert "old body line" not in result
        assert "## Other Section" in result
        assert "keep me" in result
        # 見出しが重複しないこと
        assert result.count("## AI-SDD Instructions") == 1

    def test_section_at_eof(self):
        existing = "# Project\n\n## AI-SDD Instructions (v1.0.0)\n\nold body\n"
        new = "## AI-SDD Instructions (v2.0.0)\n\nnew body\n"
        result = update_claude_md.replace_section(existing, new)
        assert "old body" not in result
        assert result.rstrip().endswith("new body")


class TestUpdateClaudeMdMain:
    """main() の分岐（作成/追記/更新/最新）を実ファイル操作で検証する。"""

    def _setup_plugin(self, tmp_path, version="9.9.9", lang="en"):
        plugin_root = tmp_path / "plugin"
        (plugin_root / ".claude-plugin").mkdir(parents=True)
        (plugin_root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"version": version}), encoding="utf-8"
        )
        template_dir = plugin_root / "skills" / "sdd-init" / "templates" / lang
        template_dir.mkdir(parents=True)
        (template_dir / "claude_md_template.md").write_text(
            "## AI-SDD Instructions (v{PLUGIN_VERSION})\n\nroot is {SDD_ROOT}\n",
            encoding="utf-8",
        )
        return plugin_root

    def _run(self, tmp_path, monkeypatch, plugin_root):
        project_root = tmp_path / "project"
        project_root.mkdir(exist_ok=True)
        (project_root / ".sdd-config.json").write_text(
            json.dumps({"lang": "en", "root": ".sdd"}), encoding="utf-8"
        )
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_root))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
        with pytest.raises(SystemExit) as exc:
            update_claude_md.main()
        assert exc.value.code == 0
        return project_root / "CLAUDE.md"

    def test_creates_new_file(self, tmp_path, monkeypatch):
        plugin_root = self._setup_plugin(tmp_path)
        claude_md = self._run(tmp_path, monkeypatch, plugin_root)
        content = claude_md.read_text(encoding="utf-8")
        assert "## AI-SDD Instructions (v9.9.9)" in content
        assert "root is .sdd" in content
        assert "{PLUGIN_VERSION}" not in content
        assert "{SDD_ROOT}" not in content

    def test_appends_when_section_absent(self, tmp_path, monkeypatch):
        plugin_root = self._setup_plugin(tmp_path)
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "CLAUDE.md").write_text("# Existing\n\ncontent\n", encoding="utf-8")

        claude_md = self._run(tmp_path, monkeypatch, plugin_root)
        content = claude_md.read_text(encoding="utf-8")
        assert "# Existing" in content
        assert "## AI-SDD Instructions (v9.9.9)" in content

    def test_updates_old_version(self, tmp_path, monkeypatch):
        plugin_root = self._setup_plugin(tmp_path)
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "CLAUDE.md").write_text(
            "# Existing\n\n## AI-SDD Instructions (v1.0.0)\n\nold\n", encoding="utf-8"
        )

        claude_md = self._run(tmp_path, monkeypatch, plugin_root)
        content = claude_md.read_text(encoding="utf-8")
        assert "## AI-SDD Instructions (v9.9.9)" in content
        assert "old" not in content
        assert content.count("## AI-SDD Instructions") == 1

    def test_skips_when_up_to_date(self, tmp_path, monkeypatch, capsys):
        plugin_root = self._setup_plugin(tmp_path)
        project_root = tmp_path / "project"
        project_root.mkdir()
        existing = "# Existing\n\n## AI-SDD Instructions (v9.9.9)\n\nkeep\n"
        (project_root / "CLAUDE.md").write_text(existing, encoding="utf-8")

        claude_md = self._run(tmp_path, monkeypatch, plugin_root)
        # 変更されないこと
        assert claude_md.read_text(encoding="utf-8") == existing
        assert "up to date" in capsys.readouterr().out

    def test_missing_plugin_json_errors(self, tmp_path, monkeypatch):
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".sdd-config.json").write_text("{}", encoding="utf-8")
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_root))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / "empty-plugin"))

        with pytest.raises(SystemExit) as exc:
            update_claude_md.main()
        assert exc.value.code == 1
