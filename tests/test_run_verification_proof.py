"""run-verification.py の proof カテゴリのユニットテスト（pytest）。

spec 3.1.1 判定表（12 行）を純粋関数 precheck / orphan_reason / needs_plain_fallback /
judge_run / aggregate で固定し、subprocess 経路は tests/fixtures/laws/fake-bend/ の
ダミー bend（PATH 先頭）で検証する。CI に本物の bend は入れない。
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = (REPO_ROOT / "plugins" / "sdd-workflow" / "skills" / "run-checklist"
               / "scripts" / "run-verification.py")
FAKE_BEND_DIR = REPO_ROOT / "tests" / "fixtures" / "laws" / "fake-bend"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_verification", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rv = _load_module()

SPEC_ID = "spec-auth-user-login"
LAWS_BODY = "import Base\nimport ./main.bend as Model\n\nlaw sort_len: (xs: List(Nat)) -> len(sort(xs)) == len(xs)\n"
PROOF_TEXT = "import Base\nimport ./LAWS.bend as Laws\nimport ./main.bend as Model\n\ndef sort_len: ...\n"
MODEL_TEXT = f"# spec: {SPEC_ID}\n# model-of: src/auth/user_login.py\n\nimport Base\ndef sort(xs): xs\n"


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _project(tmp_path: Path, *, approved=True, with_proof=True, with_model=True,
             laws_rel="laws/auth/user-login", spec_laws=None, spec_line=True) -> Path:
    """Minimal project: one spec bound to one laws directory (both directions)."""
    root = tmp_path / "proj"
    spec_laws = [laws_rel] if spec_laws is None else spec_laws
    laws_fm = "laws: [" + ", ".join(f'"{x}"' for x in spec_laws) + "]\n" if spec_laws else ""
    _write(root / ".sdd" / "specification" / "auth" / "user-login_spec.md",
           f'---\nid: "{SPEC_ID}"\ntype: "spec"\n{laws_fm}laws-status: "approved"\n---\n# x\n')
    d = root / ".sdd" / laws_rel
    header = f"# spec: {SPEC_ID}\n" if spec_line else ""
    laws = _write(d / "LAWS.bend", header + LAWS_BODY)
    if approved:
        digest = rv.law_body_hash(laws)
        laws.write_text(header + f"# approved: 2026-10-17 @reviewer sha256:{digest}\n" + LAWS_BODY,
                        encoding="utf-8")
    if with_proof:
        _write(d / "PROOF.bend", PROOF_TEXT)
    if with_model:
        _write(d / "main.bend", MODEL_TEXT)
    return root


@pytest.fixture
def fake_bend(monkeypatch, tmp_path):
    """Put the dummy bend first on PATH and return a setter for its mode."""
    monkeypatch.setenv("PATH", f"{FAKE_BEND_DIR}{os.pathsep}{os.environ.get('PATH', '')}")
    log = tmp_path / "bend.log"
    monkeypatch.setenv("FAKE_BEND_LOG", str(log))
    monkeypatch.delenv("BEND_NO_TELEMETRY", raising=False)

    def set_mode(mode: str) -> Path:
        monkeypatch.setenv("FAKE_BEND_MODE", mode)
        return log
    return set_mode


# --- precheck (rows #1-#8) ---------------------------------------------------


class TestPrecheck:
    OK = dict(bend_found=True, dir_exists=True, has_laws=True, orphan=None,
              approved="2026-10-17 @r sha256:abcdefabcdef", has_law_decl=True,
              has_proof=True, proof_imports_laws=True, bad_imports=[])

    def test_row1_tool_not_found(self):
        r = rv.precheck(**{**self.OK, "bend_found": False})
        assert r["status"] == "TOOL_NOT_FOUND"

    def test_row2_missing_dir_fails(self):
        r = rv.precheck(**{**self.OK, "bend_found": True, "dir_exists": False, "has_laws": False})
        assert r["status"] == "FAIL" and "laws:" in r["reason"]

    def test_row3_no_laws_skipped(self):
        r = rv.precheck(**{**self.OK, "has_laws": False})
        assert r["status"] == "SKIPPED" and "LAWS.bend" in r["reason"]

    def test_row4_orphan_fails_before_approval(self):
        r = rv.precheck(**{**self.OK, "orphan": "orphan laws: x", "approved": None})
        assert r == {"status": "FAIL", "reason": "orphan laws: x"}

    def test_row5_unapproved_skipped(self):
        r = rv.precheck(**{**self.OK, "approved": None, "has_proof": False, "bad_imports": ["x"]})
        assert r["status"] == "SKIPPED" and "approved" in r["reason"]

    def test_row6_no_law_decl_skipped(self):
        r = rv.precheck(**{**self.OK, "has_law_decl": False})
        assert r["status"] == "SKIPPED" and "declares no laws" in r["reason"]

    def test_row7_no_proof_fails(self):
        r = rv.precheck(**{**self.OK, "has_proof": False})
        assert r["status"] == "FAIL" and "PROOF.bend" in r["reason"]

    def test_row8_proof_not_importing_laws_fails(self):
        r = rv.precheck(**{**self.OK, "proof_imports_laws": False})
        assert r["status"] == "FAIL" and "does not import" in r["reason"]

    def test_row8_disallowed_import_fails(self):
        r = rv.precheck(**{**self.OK, "bad_imports": ["PROOF.bend: import SomePkg"]})
        assert r["status"] == "FAIL" and "import SomePkg" in r["reason"]

    def test_all_clear_runs_bend(self):
        assert rv.precheck(**self.OK) is None

    def test_order_tool_not_found_wins_over_everything(self):
        r = rv.precheck(bend_found=False, dir_exists=False, has_laws=False, orphan="o",
                        approved=None, has_law_decl=False, has_proof=False,
                        proof_imports_laws=False, bad_imports=["x"])
        assert r["status"] == "TOOL_NOT_FOUND"


# --- judge_run / needs_plain_fallback (rows #9-#12) --------------------------


class TestJudgeRun:
    def test_row9_timeout(self):
        assert rv.judge_run(None, "", True)["status"] == "TIMEOUT"

    def test_row10_pass(self):
        assert rv.judge_run(0, "...\nALL PROOFS CHECK\n", False)["status"] == "PASS"

    def test_row12_exit0_without_marker_fails(self):
        r = rv.judge_run(0, "checked 0 proofs", False)
        assert r["status"] == "FAIL" and "did not report" in r["reason"]

    def test_row12_exit1_fails(self):
        assert rv.judge_run(1, "SOME PROOFS FAIL", False)["status"] == "FAIL"

    def test_row12_exit2_fails(self):
        assert rv.judge_run(2, "", False)["status"] == "FAIL"


class TestNeedsPlainFallback:
    def test_row11_verdict_and_infra_marker(self):
        assert rv.needs_plain_fallback(1, "error: BendTT infrastructure missing", True) is True

    def test_no_fallback_without_verdict(self):
        assert rv.needs_plain_fallback(1, "BendTT infrastructure missing", False) is False

    def test_no_fallback_on_success_or_timeout(self):
        assert rv.needs_plain_fallback(0, "BendTT infrastructure", True) is False
        assert rv.needs_plain_fallback(None, "BendTT infrastructure", True) is False

    def test_no_fallback_without_marker(self):
        assert rv.needs_plain_fallback(1, "SOME PROOFS FAIL", True) is False


# --- aggregate --------------------------------------------------------------


def _r(status, laws_dir="d", verdict="not-requested", reason="why"):
    return {"status": status, "laws_dir": laws_dir, "verdict": verdict, "reason": reason}


class TestAggregate:
    @pytest.mark.parametrize("statuses,expected", [
        (["PASS", "SKIPPED"], "SKIPPED"),
        (["PASS", "TOOL_NOT_FOUND", "SKIPPED"], "TOOL_NOT_FOUND"),
        (["TIMEOUT", "TOOL_NOT_FOUND"], "TIMEOUT"),
        (["PASS", "FAIL", "TIMEOUT"], "FAIL"),
        (["PASS", "PASS"], "PASS"),
    ])
    def test_worst_status_wins(self, statuses, expected):
        results = [_r(s, laws_dir=f"d{i}") for i, s in enumerate(statuses)]
        assert rv.aggregate(results, False)["status"] == expected

    def test_reason_comes_from_worst_dir(self):
        agg = rv.aggregate([_r("PASS", "a", reason="ok"), _r("FAIL", "b", reason="boom")], False)
        assert agg["reason"] == "1 of 2 laws directories FAIL: b - boom"

    def test_verdict_three_values(self):
        assert rv.aggregate([_r("PASS")], False)["verdict"] == "not-requested"
        assert rv.aggregate([_r("PASS", verdict="checked")], True)["verdict"] == "checked"
        assert rv.aggregate([_r("PASS", verdict="checked"),
                             _r("PASS", verdict="unavailable")], True)["verdict"] == "unavailable"

    def test_empty_is_skipped(self):
        agg = rv.aggregate([], False)
        assert agg["status"] == "SKIPPED" and agg["verdict"] == "not-requested"

    def test_empty_with_verdict_requested_reports_checked(self):
        # spec 3.1.1: with --verdict the aggregate verdict is "checked" unless unavailable.
        assert rv.aggregate([], True)["verdict"] == "checked"


# --- discover_laws_dirs / build_spec_registry / orphan_reason ----------------


class TestDiscoverLawsDirs:
    def test_only_dirs_holding_laws_or_proof(self, tmp_path):
        _write(tmp_path / "laws" / "auth" / "user-login" / "LAWS.bend", "")
        _write(tmp_path / "laws" / "auth" / "signup" / "PROOF.bend", "")
        _write(tmp_path / "laws" / "misc" / "main.bend", "")  # not a laws dir
        found = rv.discover_laws_dirs(tmp_path / "laws")
        assert found == [tmp_path / "laws" / "auth" / "signup",
                         tmp_path / "laws" / "auth" / "user-login"]

    def test_missing_root(self, tmp_path):
        assert rv.discover_laws_dirs(tmp_path / "none") == []


class TestBuildSpecRegistry:
    def test_registry_shapes(self, tmp_path):
        spec = tmp_path / "specification"
        _write(spec / "a_spec.md", '---\nid: "spec-a"\nlaws: ["laws/a", "laws/a2"]\n---\n')
        _write(spec / "b.md", '---\nid: "spec-b"\nlaws: "laws/b"\n---\n')
        _write(spec / "c_spec.md", '---\nid: "spec-c"\n---\n')
        _write(spec / "nofm.md", "# no front matter\n")
        _write(spec / "noid.md", '---\ntype: "spec"\n---\n')
        reg = rv.build_spec_registry(spec)
        assert set(reg) == {"spec-a", "spec-b", "spec-c"}
        assert reg["spec-a"]["laws"] == ["laws/a", "laws/a2"]
        assert reg["spec-b"]["laws"] == ["laws/b"]
        assert reg["spec-c"]["laws"] == []
        assert reg["spec-a"]["path"] == spec / "a_spec.md"

    def test_missing_dir(self, tmp_path):
        assert rv.build_spec_registry(tmp_path / "none") == {}


class TestOrphanReason:
    REG = {"spec-a": {"path": Path("spec/a.md"), "laws": ["laws/a/", "laws/a2"]}}

    def test_bound_both_ways(self):
        assert rv.orphan_reason("spec-a", "laws/a", self.REG) is None
        assert rv.orphan_reason("spec-a", "laws/a2/", self.REG) is None

    def test_no_spec_line(self):
        assert "no '# spec:' line" in rv.orphan_reason(None, "laws/a", self.REG)

    def test_unresolved_id(self):
        r = rv.orphan_reason("spec-zzz", "laws/a", self.REG)
        assert "spec-zzz" in r and "does not resolve" in r

    def test_not_listed_in_spec_laws(self):
        r = rv.orphan_reason("spec-a", "laws/other", self.REG)
        assert "does not list 'laws/other'" in r and "spec/a.md" in r


# --- run_proof_dir end to end (fake bend) -----------------------------------


class TestRunProofDir:
    def _run(self, root: Path, laws_rel="laws/auth/user-login", verdict=False, timeout=30,
             bend_found=None):
        sdd = root / ".sdd"
        registry = rv.build_spec_registry(sdd / "specification")
        return rv.run_proof_dir(sdd / laws_rel, verdict, timeout, sdd, registry, bend_found)

    def test_pass_and_telemetry_env(self, tmp_path, fake_bend):
        log = fake_bend("pass")
        r = self._run(_project(tmp_path))
        assert r["status"] == "PASS"
        assert r["spec"] == SPEC_ID
        assert r["approved"].startswith("2026-10-17 @reviewer sha256:")
        assert r["model_of"] == ["src/auth/user_login.py"]
        assert r["command"] == "bend PROOF.bend" and r["exit_code"] == 0
        assert r["verdict"] == "not-requested"
        logged = log.read_text(encoding="utf-8")
        assert "telemetry=1" in logged
        assert logged.rstrip().endswith(str((tmp_path / "proj" / ".sdd" / "laws" / "auth" / "user-login").resolve()))

    def test_fail(self, tmp_path, fake_bend):
        fake_bend("fail")
        r = self._run(_project(tmp_path))
        assert r["status"] == "FAIL" and r["exit_code"] == 1 and "SOME PROOFS FAIL" in r["stdout"]

    def test_exit0_without_marker_fails(self, tmp_path, fake_bend):
        fake_bend("quiet")
        assert self._run(_project(tmp_path))["status"] == "FAIL"

    def test_verdict_checked(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_project(tmp_path), verdict=True)
        assert r["status"] == "PASS" and r["verdict"] == "checked"
        assert r["command"] == "bend --verdict PROOF.bend"

    def test_verdict_infra_missing_falls_back(self, tmp_path, fake_bend):
        log = fake_bend("infra")
        r = self._run(_project(tmp_path), verdict=True)
        assert r["status"] == "PASS" and r["verdict"] == "unavailable"
        assert r["command"] == "bend PROOF.bend"  # the fallback run is what was judged
        assert log.read_text(encoding="utf-8").count("args=") == 2

    def test_timeout(self, tmp_path, fake_bend, monkeypatch):
        fake_bend("sleep")
        monkeypatch.setenv("FAKE_BEND_SLEEP", "3")
        r = self._run(_project(tmp_path), timeout=1)
        assert r["status"] == "TIMEOUT"

    def test_tool_not_found_without_bend(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
        r = self._run(_project(tmp_path))
        assert r["status"] == "TOOL_NOT_FOUND"

    def test_missing_dir_fails(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_project(tmp_path), laws_rel="laws/auth/typo")
        assert r["status"] == "FAIL" and "not found" in r["reason"]

    def test_no_laws_file_skipped(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path)
        (root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend").unlink()
        r = self._run(root)
        assert r["status"] == "SKIPPED" and r["spec"] is None

    def test_orphan_without_spec_line(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_project(tmp_path, spec_line=False))
        assert r["status"] == "FAIL" and "no '# spec:' line" in r["reason"]

    def test_orphan_unresolved_id(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path)
        laws = root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
        laws.write_text(laws.read_text(encoding="utf-8").replace(SPEC_ID, "spec-ghost", 1),
                        encoding="utf-8")
        r = self._run(root)
        assert r["status"] == "FAIL" and "spec-ghost" in r["reason"]

    def test_orphan_not_listed_in_spec(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_project(tmp_path, spec_laws=["laws/auth/other"]))
        assert r["status"] == "FAIL" and "does not list" in r["reason"]

    def test_orphan_evaluated_before_approval(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_project(tmp_path, approved=False, spec_laws=[]))
        assert r["status"] == "FAIL" and "orphan laws" in r["reason"]

    def test_outside_sdd_root_is_orphan(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path)
        outside = tmp_path / "elsewhere"
        _write(outside / "LAWS.bend", f"# spec: {SPEC_ID}\n" + LAWS_BODY)
        registry = rv.build_spec_registry(root / ".sdd" / "specification")
        r = rv.run_proof_dir(outside, False, 30, root / ".sdd", registry, True)
        assert r["status"] == "FAIL" and "does not list" in r["reason"]

    def test_unapproved_skipped_with_current_hash(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path, approved=False)
        r = self._run(root)
        digest = rv.law_body_hash(root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend")
        assert r["status"] == "SKIPPED" and f"sha256:{digest}" in r["reason"]
        assert r["approved"] is None

    def test_body_change_expires_approval(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path)
        laws = root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
        laws.write_text(laws.read_text(encoding="utf-8").replace("== len(xs)", "== 0"),
                        encoding="utf-8")
        r = self._run(root)
        assert r["status"] == "SKIPPED" and "Current law-body hash" in r["reason"]

    def test_no_law_declaration_skipped(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path)
        laws = root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
        body = "import Base\nimport ./main.bend as Model\n\ndef nothing: 1\n"
        laws.write_text(f"# spec: {SPEC_ID}\n" + LAWS_BODY, encoding="utf-8")
        digest = rv.law_body_hash(_write(laws, f"# spec: {SPEC_ID}\n" + body))
        laws.write_text(f"# spec: {SPEC_ID}\n# approved: 2026-10-17 @r sha256:{digest}\n" + body,
                        encoding="utf-8")
        r = self._run(root)
        assert r["status"] == "SKIPPED" and "declares no laws" in r["reason"]

    def test_missing_proof_fails(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_project(tmp_path, with_proof=False))
        assert r["status"] == "FAIL" and "PROOF.bend is missing" in r["reason"]

    def test_proof_not_importing_laws_fails(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path)
        _write(root / ".sdd" / "laws" / "auth" / "user-login" / "PROOF.bend", "import Base\n")
        r = self._run(root)
        assert r["status"] == "FAIL" and "does not import LAWS.bend" in r["reason"]

    def test_disallowed_import_fails_before_bend(self, tmp_path, fake_bend):
        log = fake_bend("pass")
        root = _project(tmp_path)
        _write(root / ".sdd" / "laws" / "auth" / "user-login" / "PROOF.bend",
               "import ./LAWS.bend as Laws\nimport @hub/sort\n")
        r = self._run(root)
        assert r["status"] == "FAIL" and "import @hub/sort" in r["reason"]
        assert not log.exists()

    def test_model_optional(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _project(tmp_path, with_model=False)
        _write(root / ".sdd" / "laws" / "auth" / "user-login" / "PROOF.bend", "import ./LAWS.bend as Laws\n")
        laws = root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
        text = laws.read_text(encoding="utf-8").replace("import ./main.bend as Model\n", "")
        body = text.split("\n", 2)[2]
        digest = rv.law_body_hash(_write(laws, body))
        laws.write_text(f"# spec: {SPEC_ID}\n# approved: 2026-10-17 @r sha256:{digest}\n" + body,
                        encoding="utf-8")
        r = self._run(root)
        assert r["status"] == "PASS" and r["model_of"] == []


# --- CLI --------------------------------------------------------------------


def _cli(cwd: Path, *args: str, env=None) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run([sys.executable, str(SCRIPT_PATH), *args], cwd=cwd, env=full_env,
                          capture_output=True, text=True, timeout=60)


class TestProofCli:
    def test_explicit_dirs_aggregate(self, tmp_path):
        root = _project(tmp_path)
        _write(root / ".sdd" / "laws" / "auth" / "signup" / "LAWS.bend", "# spec: spec-ghost\nlaw a: 1\n")
        env = {"PATH": f"{FAKE_BEND_DIR}{os.pathsep}{os.environ['PATH']}", "FAKE_BEND_MODE": "pass"}
        p = _cli(root, "proof", "--laws-dir", ".sdd/laws/auth/user-login",
                 "--laws-dir", ".sdd/laws/auth/signup", env=env)
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert out["category"] == "proof" and out["status"] == "FAIL"
        assert out["verdict"] == "not-requested" and out["timeout_seconds"] == 300
        assert out["note"] == rv.PASS_NOTE
        statuses = {r["laws_dir"]: r["status"] for r in out["results"]}
        assert statuses == {os.path.join(".sdd", "laws", "auth", "user-login"): "PASS",
                            os.path.join(".sdd", "laws", "auth", "signup"): "FAIL"}

    def test_discovery_under_sdd_laws_path(self, tmp_path):
        root = _project(tmp_path)
        env = {"PATH": f"{FAKE_BEND_DIR}{os.pathsep}{os.environ['PATH']}", "FAKE_BEND_MODE": "pass"}
        out = json.loads(_cli(root, "proof", env=env).stdout)
        assert out["status"] == "PASS"
        assert [r["laws_dir"] for r in out["results"]] == [os.path.join(".sdd", "laws", "auth", "user-login")]

    def test_discovery_with_no_laws_dir_is_skipped(self, tmp_path):
        root = tmp_path / "empty"
        root.mkdir()
        out = json.loads(_cli(root, "proof").stdout)
        assert out["status"] == "SKIPPED" and out["results"] == []

    def test_without_bend_is_tool_not_found(self, tmp_path):
        root = _project(tmp_path)
        out = json.loads(_cli(root, "proof", env={"PATH": str(tmp_path / "nobin")}).stdout)
        assert out["status"] == "TOOL_NOT_FOUND"
        assert out["results"][0]["status"] == "TOOL_NOT_FOUND"

    def test_print_laws_hash(self, tmp_path):
        root = _project(tmp_path, approved=False)
        out = json.loads(_cli(root, "proof", "--print-laws-hash",
                              "--laws-dir", ".sdd/laws/auth/user-login").stdout)
        digest = rv.law_body_hash(root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend")
        assert out == {"category": "proof",
                       "laws_hash": {os.path.join(".sdd", "laws", "auth", "user-login"): digest}}

    def test_config_and_cli_precedence(self, tmp_path):
        root = _project(tmp_path)
        (root / ".sdd-config.json").write_text(
            json.dumps({"proof": {"timeout_seconds": 42, "verdict": True}}), encoding="utf-8")
        env = {"PATH": f"{FAKE_BEND_DIR}{os.pathsep}{os.environ['PATH']}", "FAKE_BEND_MODE": "pass"}
        out = json.loads(_cli(root, "proof", env=env).stdout)
        assert out["timeout_seconds"] == 42 and out["verdict"] == "checked"
        out = json.loads(_cli(root, "proof", "--timeout", "7", env=env).stdout)
        assert out["timeout_seconds"] == 7

    def test_custom_laws_directory_name(self, tmp_path):
        root = _project(tmp_path, laws_rel="proofs/auth/user-login")
        (root / ".sdd-config.json").write_text(
            json.dumps({"directories": {"laws": "proofs"}}), encoding="utf-8")
        env = {"PATH": f"{FAKE_BEND_DIR}{os.pathsep}{os.environ['PATH']}", "FAKE_BEND_MODE": "pass"}
        out = json.loads(_cli(root, "proof", env=env).stdout)
        assert out["status"] == "PASS"


class TestLegacyCategoriesUnchanged:
    def test_single_positional_argument_still_works(self, tmp_path):
        p = _cli(tmp_path, "test")
        assert p.returncode == 0
        out = json.loads(p.stdout)
        assert out["category"] == "test" and out["status"] == "SKIPPED"
        assert "project_type" in out

    def test_bad_usage_exits_2(self, tmp_path):
        assert _cli(tmp_path, "test", "--extra").returncode == 2
        assert _cli(tmp_path, "bogus").returncode == 2
        assert "proof" in _cli(tmp_path).stderr


# --- FR-013 warnings (laws-drafting_spec) -------------------------------------

DRIFT_SPEC_BODY = "# 3. 要求\n\n## 3.1. 機能\n\n本文\n"


def _drift_project(tmp_path: Path, *, source_hash=None, approved=True, source_line=True):
    """Project whose spec has section 3.1 and whose LAWS.bend cites it."""
    root = _project(tmp_path, approved=False)
    spec = root / ".sdd" / "specification" / "auth" / "user-login_spec.md"
    spec.write_text(spec.read_text(encoding="utf-8") + DRIFT_SPEC_BODY, encoding="utf-8")
    import laws_drafting as ld
    digest = source_hash or ld.section_hash(spec.read_text(encoding="utf-8"), "3.1")
    laws = root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
    src = f"# source: {SPEC_ID} §3.1 sha256:{digest}\n" if source_line else ""
    body = f"# spec: {SPEC_ID}\n@@A@@import Base\nimport ./main.bend as Model\n\n{src}law a:\n  for xs: Nat\n  {{xs == xs : Nat}}\n"
    laws.write_text(body.replace("@@A@@", ""), encoding="utf-8")
    if approved:
        h = rv.law_body_hash(laws)
        laws.write_text(body.replace("@@A@@", f"# approved: 2026-10-17 @r sha256:{h}\n"),
                        encoding="utf-8")
    return root


class TestDriftWarnings:
    _run = TestRunProofDir._run

    def test_no_warnings_key_when_in_sync(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_drift_project(tmp_path))
        assert r["status"] == "PASS" and "warnings" not in r

    def test_drift_adds_warning_without_changing_status(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_drift_project(tmp_path, source_hash="0" * 12))
        assert r["status"] == "PASS"
        assert r["warnings"] == [{"code": "source_drift", "law": "a", "source": "3.1"}]

    def test_warning_on_fail_keeps_fail(self, tmp_path, fake_bend):
        fake_bend("fail")
        r = self._run(_drift_project(tmp_path, source_hash="0" * 12))
        assert r["status"] == "FAIL" and len(r["warnings"]) == 1

    def test_unapproved_directory_has_no_warnings(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_drift_project(tmp_path, source_hash="0" * 12, approved=False))
        assert r["status"] == "SKIPPED" and "warnings" not in r

    def test_hand_written_laws_without_source_are_exempt(self, tmp_path, fake_bend):
        fake_bend("pass")
        r = self._run(_drift_project(tmp_path, source_line=False))
        assert "warnings" not in r

    def test_no_bend_no_warnings(self, tmp_path):
        r = self._run(_drift_project(tmp_path, source_hash="0" * 12), bend_found=False)
        assert r["status"] == "TOOL_NOT_FOUND" and "warnings" not in r

    def test_expired_approval_has_no_warnings(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _drift_project(tmp_path, source_hash="0" * 12)
        laws = root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
        laws.write_text(laws.read_text(encoding="utf-8") + "\n# edited\nlaw b:\n  for x: Nat\n  {x == x : Nat}\n",
                        encoding="utf-8")
        r = self._run(root)
        assert r["status"] == "SKIPPED" and "warnings" not in r

    def test_malformed_source_reports_source_invalid(self, tmp_path, fake_bend):
        fake_bend("pass")
        root = _drift_project(tmp_path, approved=False)
        laws = root / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
        text = laws.read_text(encoding="utf-8")
        import re
        text = re.sub(r"# source: .*", "# source: not-a-valid-source", text)
        laws.write_text(text, encoding="utf-8")
        h = rv.law_body_hash(laws)
        laws.write_text(text.replace("import Base", f"# approved: 2026-10-17 @r sha256:{h}\nimport Base", 1),
                        encoding="utf-8")
        r = self._run(root)
        assert r["status"] == "PASS"
        assert [w["code"] for w in r["warnings"]] == ["source_invalid"]
