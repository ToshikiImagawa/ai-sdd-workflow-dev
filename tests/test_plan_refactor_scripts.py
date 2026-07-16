"""plan-refactor スクリプト（Python 移植版）のユニットテスト（pytest）。

bash 版 find-implementation-files.sh / scan-existing-docs.sh を Python に
移植した find-implementation-files.py / scan-existing-docs.py を検証する。
探索結果（実装ファイル一覧・既存ドキュメント一覧）・キャッシュ配置・JSON 出力・
終了コードが移植前と一致することを確認する。
"""

import importlib.util
import json
import os
from pathlib import Path

import pytest

SKILL_SCRIPTS = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "skills" / "plan-refactor" / "scripts"
)
FIND_SCRIPT = SKILL_SCRIPTS / "find-implementation-files.py"
SCAN_SCRIPT = SKILL_SCRIPTS / "scan-existing-docs.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


find_impl = _load_module("find_implementation_files", FIND_SCRIPT)
scan_docs = _load_module("scan_existing_docs", SCAN_SCRIPT)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """テスト間で SDD_* / CLAUDE_* 環境変数が漏れないようにクリアする。"""
    for key in (
        "SDD_ROOT",
        "SDD_REQUIREMENT_DIR",
        "SDD_SPECIFICATION_DIR",
        "SDD_REQUIREMENT_PATH",
        "SDD_SPECIFICATION_PATH",
        "CLAUDE_PROJECT_DIR",
    ):
        monkeypatch.delenv(key, raising=False)


def _run(module, argv, project_dir, monkeypatch, env=None):
    """スクリプトの main() を argv / env を差し替えて実行する。"""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_dir))
    for key, value in (env or {}).items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr("sys.argv", argv)
    module.main()


# --- scan-existing-docs.py -------------------------------------------------


class TestScanExistingDocs:
    def test_requires_feature_name(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["scan-existing-docs.py"])
        with pytest.raises(SystemExit) as exc:
            scan_docs.main()
        assert exc.value.code == 1

    def test_structure_none(self, tmp_path, monkeypatch):
        _run(scan_docs, ["scan", "auth"], tmp_path, monkeypatch)
        result = json.loads(
            (tmp_path / ".sdd" / ".cache" / "plan-refactor" / "existing-docs.json")
            .read_text(encoding="utf-8")
        )
        assert result == {
            "prd_exists": False,
            "spec_exists": False,
            "design_exists": False,
            "prd_path": "",
            "spec_path": "",
            "design_path": "",
            "structure": "none",
            "feature_name": "auth",
        }

    def test_flat_structure(self, tmp_path, monkeypatch):
        req = tmp_path / ".sdd" / "requirement"
        spec = tmp_path / ".sdd" / "specification"
        req.mkdir(parents=True)
        spec.mkdir(parents=True)
        (req / "auth.md").write_text("prd", encoding="utf-8")
        (spec / "auth_spec.md").write_text("spec", encoding="utf-8")
        (spec / "auth_design.md").write_text("design", encoding="utf-8")

        _run(scan_docs, ["scan", "auth"], tmp_path, monkeypatch)
        result = json.loads(
            (tmp_path / ".sdd" / ".cache" / "plan-refactor" / "existing-docs.json")
            .read_text(encoding="utf-8")
        )
        assert result["structure"] == "flat"
        assert result["prd_exists"] is True
        assert result["spec_exists"] is True
        assert result["design_exists"] is True
        assert result["prd_path"] == str(req / "auth.md")
        assert result["spec_path"] == str(spec / "auth_spec.md")
        assert result["design_path"] == str(spec / "auth_design.md")

    def test_flat_spec_only(self, tmp_path, monkeypatch):
        spec = tmp_path / ".sdd" / "specification"
        spec.mkdir(parents=True)
        (spec / "auth_spec.md").write_text("spec", encoding="utf-8")

        _run(scan_docs, ["scan", "auth"], tmp_path, monkeypatch)
        result = json.loads(
            (tmp_path / ".sdd" / ".cache" / "plan-refactor" / "existing-docs.json")
            .read_text(encoding="utf-8")
        )
        assert result["structure"] == "flat"
        assert result["spec_exists"] is True
        assert result["prd_exists"] is False
        assert result["design_exists"] is False

    def test_hierarchical_child(self, tmp_path, monkeypatch):
        req = tmp_path / ".sdd" / "requirement" / "auth"
        spec = tmp_path / ".sdd" / "specification" / "auth"
        req.mkdir(parents=True)
        spec.mkdir(parents=True)
        (req / "user-login.md").write_text("prd", encoding="utf-8")
        (spec / "user-login_design.md").write_text("design", encoding="utf-8")

        _run(scan_docs, ["scan", "auth/user-login"], tmp_path, monkeypatch)
        result = json.loads(
            (tmp_path / ".sdd" / ".cache" / "plan-refactor" / "existing-docs.json")
            .read_text(encoding="utf-8")
        )
        assert result["structure"] == "hierarchical"
        assert result["prd_exists"] is True
        assert result["design_exists"] is True
        assert result["spec_exists"] is False
        assert result["feature_name"] == "auth/user-login"

    def test_hierarchical_parent_index(self, tmp_path, monkeypatch):
        spec = tmp_path / ".sdd" / "specification" / "auth"
        spec.mkdir(parents=True)
        (spec / "index_spec.md").write_text("spec", encoding="utf-8")

        _run(scan_docs, ["scan", "auth"], tmp_path, monkeypatch)
        result = json.loads(
            (tmp_path / ".sdd" / ".cache" / "plan-refactor" / "existing-docs.json")
            .read_text(encoding="utf-8")
        )
        assert result["structure"] == "hierarchical-parent"
        assert result["spec_exists"] is True
        assert result["spec_path"] == str(spec / "index_spec.md")

    def test_custom_sdd_root(self, tmp_path, monkeypatch):
        req = tmp_path / "docs" / "requirement"
        req.mkdir(parents=True)
        (req / "auth.md").write_text("prd", encoding="utf-8")

        _run(scan_docs, ["scan", "auth"], tmp_path, monkeypatch, env={"SDD_ROOT": "docs"})
        # キャッシュは設定 root 配下に生成される
        result = json.loads(
            (tmp_path / "docs" / ".cache" / "plan-refactor" / "existing-docs.json")
            .read_text(encoding="utf-8")
        )
        assert result["structure"] == "flat"
        assert result["prd_exists"] is True


# --- find-implementation-files.py: 純粋関数 --------------------------------


class TestCategorize:
    def test_test_files(self):
        impl, test, config = find_impl.categorize(
            [
                "./src/auth.test.ts",
                "./src/auth.spec.js",
                "./__tests__/auth.ts",
                "./tests/auth.py",
                "./test/helper.rb",
            ]
        )
        assert impl == []
        assert config == []
        assert len(test) == 5

    def test_config_files(self):
        impl, test, config = find_impl.categorize(
            ["./package.json", "./tsconfig.json", "./config.yml", "./Cargo.lock"]
        )
        assert impl == []
        assert test == []
        assert len(config) == 4

    def test_implementation_files(self):
        impl, test, config = find_impl.categorize(
            ["./src/auth.ts", "./lib/auth.py", "./app/auth.go"]
        )
        assert len(impl) == 3
        assert test == []
        assert config == []

    def test_test_takes_priority_over_config(self):
        # /tests/ を含むパスは拡張子が .json でも test に分類される
        impl, test, config = find_impl.categorize(["./tests/fixtures/data.json"])
        assert test == ["./tests/fixtures/data.json"]
        assert config == []


# --- find-implementation-files.py: 統合 ------------------------------------


def _read_json(project_dir):
    return json.loads(
        (project_dir / ".sdd" / ".cache" / "plan-refactor" / "implementation-files.json")
        .read_text(encoding="utf-8")
    )


def _read_lines(project_dir, name):
    text = (
        project_dir / ".sdd" / ".cache" / "plan-refactor" / name
    ).read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line]


class TestFindImplementationFiles:
    def test_requires_feature_name(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["find-implementation-files.py"])
        with pytest.raises(SystemExit) as exc:
            find_impl.main()
        assert exc.value.code == 1

    def test_match_by_name(self, tmp_path, monkeypatch):
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth.ts").write_text("nothing", encoding="utf-8")
        (src / "unrelated.ts").write_text("nothing", encoding="utf-8")

        _run(find_impl, ["find", "auth"], tmp_path, monkeypatch)
        all_files = _read_lines(tmp_path, "all-files.txt")
        assert any(f.endswith("auth.ts") for f in all_files)
        assert not any(f.endswith("unrelated.ts") for f in all_files)

    def test_match_by_content_case_insensitive(self, tmp_path, monkeypatch):
        src = tmp_path / "src"
        src.mkdir()
        (src / "handler.ts").write_text("import Auth from './x'", encoding="utf-8")
        (src / "other.ts").write_text("nothing here", encoding="utf-8")

        _run(find_impl, ["find", "auth"], tmp_path, monkeypatch)
        all_files = _read_lines(tmp_path, "all-files.txt")
        # 大文字小文字を無視して内容一致（grep -i 相当）
        assert any(f.endswith("handler.ts") for f in all_files)
        assert not any(f.endswith("other.ts") for f in all_files)

    def test_excludes_node_modules(self, tmp_path, monkeypatch):
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "auth.ts").write_text("auth", encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth.ts").write_text("auth", encoding="utf-8")

        _run(find_impl, ["find", "auth"], tmp_path, monkeypatch)
        all_files = _read_lines(tmp_path, "all-files.txt")
        # node_modules 配下は除外される（tmp ディレクトリ名との誤検出を避けるため
        # パスセグメント単位で検証する）
        assert not any(f"{os.sep}node_modules{os.sep}" in f for f in all_files)
        assert any(f.endswith(f"src{os.sep}auth.ts") for f in all_files)

    def test_json_counts_and_categorization(self, tmp_path, monkeypatch):
        src = tmp_path / "src"
        tests = tmp_path / "src" / "__tests__"
        src.mkdir()
        tests.mkdir()
        (src / "auth.ts").write_text("x", encoding="utf-8")
        (tests / "auth.test.ts").write_text("x", encoding="utf-8")
        (src / "auth.config.json").write_text("{}", encoding="utf-8")

        _run(find_impl, ["find", "auth"], tmp_path, monkeypatch)
        result = _read_json(tmp_path)
        assert result["feature_name"] == "auth"
        assert result["scope_dir"] == "all"
        assert result["file_count"] == 3
        assert result["implementation_count"] == 1
        assert result["test_count"] == 1
        assert result["config_count"] == 1
        # リストパスがキャッシュディレクトリを指す
        assert result["files_list_path"].endswith("all-files.txt")

    def test_scope_dir_limits_search(self, tmp_path, monkeypatch):
        src = tmp_path / "src"
        other = tmp_path / "other"
        src.mkdir()
        other.mkdir()
        (src / "auth.ts").write_text("auth", encoding="utf-8")
        (other / "auth.ts").write_text("auth", encoding="utf-8")

        _run(find_impl, ["find", "auth", "src"], tmp_path, monkeypatch)
        result = _read_json(tmp_path)
        assert result["scope_dir"] == "src"
        all_files = _read_lines(tmp_path, "all-files.txt")
        assert all("other" not in f for f in all_files)
        assert any("auth.ts" in f for f in all_files)

    def test_dedup_name_and_content(self, tmp_path, monkeypatch):
        src = tmp_path / "src"
        src.mkdir()
        # 名前・内容の両方でマッチしても all-files では一意
        (src / "auth.ts").write_text("auth feature", encoding="utf-8")

        _run(find_impl, ["find", "auth"], tmp_path, monkeypatch)
        result = _read_json(tmp_path)
        assert result["file_count"] == 1
        assert result["files_by_name_count"] == 1
        assert result["files_by_content_count"] == 1

    def test_content_fallback_when_no_common_dirs(self, tmp_path, monkeypatch):
        # src/lib 等が存在しない場合はプロジェクト全体を内容検索する
        (tmp_path / "main.ts").write_text("auth logic", encoding="utf-8")

        _run(find_impl, ["find", "auth"], tmp_path, monkeypatch)
        all_files = _read_lines(tmp_path, "all-files.txt")
        assert any(f.endswith("main.ts") for f in all_files)
