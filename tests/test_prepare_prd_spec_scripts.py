"""generate-prd / generate-spec の prepare-*.py ヘルパースクリプトのユニットテスト（pytest）。

read_config() が .sdd-config.json 不在時にハード停止せず、hook_common.resolve_lang_and_root() 経由で
SDD_LANG/SDD_ROOT 環境変数またはデフォルト値へフォールバックすることを検証する。
"""

import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = (
    Path(__file__).resolve().parent.parent / "plugins" / "sdd-workflow"
)
PREPARE_PRD = (
    PLUGIN_ROOT / "skills" / "generate-prd" / "scripts" / "prepare-prd.py"
)
PREPARE_SPEC = (
    PLUGIN_ROOT / "skills" / "generate-spec" / "scripts" / "prepare-spec.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prd = _load_module("prepare_prd", PREPARE_PRD)
spec_mod = _load_module("prepare_spec", PREPARE_SPEC)


class TestPreparePrdReadConfig:
    def test_missing_config_falls_back_to_defaults(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SDD_LANG", raising=False)
        monkeypatch.delenv("SDD_ROOT", raising=False)
        assert prd.read_config(tmp_path) == {"lang": "en", "root": ".sdd"}

    def test_missing_config_falls_back_to_env_vars(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SDD_LANG", "ja")
        monkeypatch.setenv("SDD_ROOT", ".ai-docs")
        assert prd.read_config(tmp_path) == {"lang": "ja", "root": ".ai-docs"}

    def test_config_file_takes_priority_over_env_vars(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SDD_LANG", "ja")
        (tmp_path / ".sdd-config.json").write_text(
            json.dumps({"lang": "en", "root": ".sdd"}), encoding="utf-8"
        )
        assert prd.read_config(tmp_path) == {"lang": "en", "root": ".sdd"}


class TestPrepareSpecReadConfig:
    def test_missing_config_falls_back_to_defaults(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SDD_LANG", raising=False)
        monkeypatch.delenv("SDD_ROOT", raising=False)
        assert spec_mod.read_config(tmp_path) == {"lang": "en", "root": ".sdd"}
