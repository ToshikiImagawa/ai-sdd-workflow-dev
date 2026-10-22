"""spec-task-implementation-proof-gate の法則を実装に対して検証する差分テスト。

.sdd/laws/task-implementation/proof-gate/LAWS.bend の 5 法則（第 1 弾の手書き法則。全称法則 4 件と空入力 1 件で、
いずれも Bend に残る）を、参照モデルではなく実装 run-verification.py に対して assert する。
全称法則は有限の値域（判定 5 種・真偽値）を列挙して検証する。順位の符号化（PASS=0 SKIPPED=1 FAIL=4）は使わず、
実装の status 文字列で書く。bend は不要。
"""
# spec: spec-task-implementation-proof-gate
# impl-of: plugins/sdd-workflow/skills/run-checklist/scripts/run-verification.py

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins" / "sdd-workflow"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run_verification = _load(
    "run_verification", PLUGIN / "skills" / "run-checklist" / "scripts" / "run-verification.py")

STATUSES = list(run_verification.SEVERITY)


def _agg(statuses):
    results = [{"status": s, "laws_dir": f"d{i}", "reason": "r", "verdict": "not-requested"}
               for i, s in enumerate(statuses)]
    return run_verification.aggregate(results, False)["status"]


# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
def test_agg_empty_skipped():
    assert _agg([]) == "SKIPPED"


# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
@pytest.mark.parametrize("x", STATUSES)
def test_agg_single_identity(x):
    assert _agg([x]) == x


# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
@pytest.mark.parametrize("a", STATUSES)
@pytest.mark.parametrize("b", STATUSES)
def test_agg_pair_commutes(a, b):
    assert _agg([a, b]) == _agg([b, a])


# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
def test_unapproved_never_pass():
    # approved=None → precheck が bend 実行前に SKIPPED を返す（exit code / marker は到達しない）
    r = run_verification.precheck(
        bend_found=True, dir_exists=True, has_laws=True, orphan=None,
        approved=None, has_law_decl=True, has_proof=True,
        proof_imports_laws=True, bad_imports=[])
    assert r["status"] == "SKIPPED"


# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
@pytest.mark.parametrize("exit_code", [0, 1])
def test_pass_requires_marker(exit_code):
    r = run_verification.judge_run(exit_code, "some output without the marker", False)
    assert r["status"] == "FAIL"
