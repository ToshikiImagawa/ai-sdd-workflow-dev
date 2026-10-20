"""draft_laws.py (skills/draft-laws/scripts) のユニットテスト（pytest）。

max_laws 読み込み、候補の決定的な整列・上限、status の状態判定、check、
および第 1 弾の 5 法則との命題一致（laws-drafting_spec §11 検収の bend 不要部分）を検証する。
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/sdd-workflow/skills/draft-laws/scripts/draft_laws.py"
FIXTURES = ROOT / "tests/fixtures/draft-laws"
REFERENCE = ROOT / ".sdd/laws/task-implementation/proof-gate/LAWS.bend"

spec = importlib.util.spec_from_file_location("draft_laws", SCRIPT)
dl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dl)

SPEC_TEXT = """---
id: "spec-demo"
laws: ["laws/demo"]
laws-status: drafted
---

# 1. A

text

# 2. B

## 2.1. Rules

rule one
"""


def run(*args, cwd=None):
    r = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd,
                       capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


@pytest.mark.parametrize("raw,expected,warns", [
    ({}, 10, False),
    ({"laws": {"max_laws": 3}}, 3, False),
    ({"laws": {"max_laws": 0}}, 10, True),
    ({"laws": {"max_laws": -1}}, 10, True),
    ({"laws": {"max_laws": 2.5}}, 10, True),
    ({"laws": {"max_laws": "5"}}, 10, True),
    ({"laws": {"max_laws": True}}, 10, True),
])
def test_load_max_laws(raw, expected, warns):
    value, warning = dl.load_max_laws(raw)
    assert value == expected
    assert (warning is not None) == warns


def test_rank_is_deterministic_and_cuts_off():
    cands = [
        {"name": "c", "section": "3.1.10", "priority": 2, "body": "c"},
        {"name": "b", "section": "3.1.2", "priority": 2, "body": "b"},
        {"name": "a", "section": "9", "priority": 1, "body": "a"},
        {"name": "t", "section": "1", "priority": 1, "body": "t", "trivial": True},
        {"name": "d", "section": "3.1.3", "priority": 2, "body": " b "},
    ]
    out = dl.rank_candidates(cands, 2)
    assert [c["name"] for c in out["adopted"]] == ["a", "b"]
    reasons = {c["name"]: c["reason"] for c in out["not_adopted"]}
    assert reasons == {"t": "trivial", "d": "duplicate", "c": "limit"}
    assert dl.rank_candidates(list(reversed(cands)), 2) == out


def test_rank_empty():
    assert dl.rank_candidates([], 10)["adopted"] == []


def _project(tmp_path, laws_text=None, config=None):
    spec = tmp_path / ".sdd/specification/demo_spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(SPEC_TEXT, encoding="utf-8")
    if laws_text is not None:
        laws = tmp_path / ".sdd/laws/demo/LAWS.bend"
        laws.parent.mkdir(parents=True)
        laws.write_text(laws_text, encoding="utf-8")
    if config is not None:
        (tmp_path / ".sdd-config.json").write_text(json.dumps(config), encoding="utf-8")
    return spec


def test_status_none_and_missing_spec(tmp_path):
    _project(tmp_path)
    rc, out = run("status", "demo", "--project-root", str(tmp_path))
    assert rc == 0 and out["laws_state"] == "none" and out["write_target"] == "LAWS.bend"
    assert out["model_allowed"] is False
    rc, out = run("status", "nope", "--project-root", str(tmp_path))
    assert rc == 1 and "spec not found" in out["error"]


def test_status_drafted_then_valid_then_mismatch(tmp_path):
    body = "import Base\n\nlaw x:\n  {1n == 1n : Nat}\n"
    laws = "# spec: spec-demo\n#\n" + body
    _project(tmp_path, laws, {"laws": {"max_laws": 0}})
    rc, out = run("status", "demo", "--project-root", str(tmp_path))
    assert out["laws_state"] == "drafted" and out["write_target"] == "LAWS.draft.bend"
    assert out["model_refusal"] == "LAWS.bend has no approval line"
    assert out["approval_format"].startswith("# approved: YYYY-MM-DD <approver> sha256:")
    assert out["current_hash"] in out["approval_format"]
    rc, ow = run("status", "demo", "--project-root", str(tmp_path), "--overwrite")
    assert ow["write_target"] == "LAWS.bend" and "overwrite_refused" not in ow
    assert any("max_laws" in w for w in out["warnings"]) and out["max_laws"] == 10
    h = out["current_hash"]
    path = tmp_path / ".sdd/laws/demo/LAWS.bend"
    path.write_text(f"# spec: spec-demo\n# approved: 2026-01-01 @me sha256:{h}\n" + body)
    rc, out = run("status", "demo", "--project-root", str(tmp_path))
    assert out["laws_state"] == "approved" and out["model_allowed"] is True
    rc, ow = run("status", "demo", "--project-root", str(tmp_path), "--overwrite")
    assert ow["write_target"] == "LAWS.draft.bend" and "approval line" in ow["overwrite_refused"]
    assert out["write_target"] == "LAWS.draft.bend"
    path.write_text(f"# spec: spec-demo\n# approved: 2026-01-01 @me sha256:{h}\n" + body + "# x\nlaw y:\n  {2n == 2n : Nat}\n")
    rc, out = run("status", "demo", "--project-root", str(tmp_path))
    assert out["laws_state"] == "mismatch" and out["model_allowed"] is False
    assert out["write_target"] == "LAWS.draft.bend" and out["current_hash"] != h
    assert h not in out["approval_format"] and out["current_hash"] in out["approval_format"]
    rc, ow = run("status", "demo", "--project-root", str(tmp_path), "--overwrite")
    assert ow["write_target"] == "LAWS.draft.bend" and "overwrite_refused" in ow


def test_status_orphan_warning(tmp_path):
    spec = _project(tmp_path, "# spec: spec-demo\n#\nimport Base\n")
    spec.write_text(SPEC_TEXT.replace('["laws/demo"]', "[]"), encoding="utf-8")
    _, out = run("status", "demo", "--project-root", str(tmp_path))
    assert any("orphan" in w for w in out["warnings"])


def test_hash_and_check(tmp_path):
    spec = _project(tmp_path)
    _, h = run("hash", str(spec), "2.1")
    assert h["ok"] and len(h["hash"]) == 12
    laws = tmp_path / "LAWS.bend"
    text = (f"# spec: spec-demo\n#\nimport Base\nimport ./main.bend as Model\n\n"
            f"# model-api: Model.f(x: Nat) -> Nat\n\n"
            f"# source: spec-demo §2.1 sha256:{h['hash']}\nlaw l:\n  for x: Nat\n  {{Model.f(x) == x : Nat}}\n")
    laws.write_text(text, encoding="utf-8")
    _, out = run("check", str(laws), "--spec", str(spec))
    assert out["errors"] == 0 and out["propose_drafted"] is True
    laws.write_text(text.replace(h["hash"], "0" * 12), encoding="utf-8")
    _, out = run("check", str(laws), "--spec", str(spec))
    assert out["propose_drafted"] is False
    assert {f["code"] for f in out["findings"]} == {"source_drift"}


def _acceptance():
    gen = FIXTURES / "proof-gate-acceptance.LAWS.draft.bend"
    result = dl.cmd_compare(type("N", (), {"generated": str(gen), "reference": str(REFERENCE)}))
    return gen, {r["law"]: r for r in result["results"]}, result


def test_acceptance_independent_reproduction_correspondence():
    """laws-drafting_spec §11 (independent re-run, 7 laws drafted from proof-gate_spec).

    Pinned correspondence with the first-wave laws: 4 of 5 are covered, 1 is not
    reproduced. The overall ``passed`` is therefore False by design: the spec's
    one-way criterion is NOT met, and this test records that result.
    """
    gen, rows, result = _acceptance()
    drafted = {law.name: law.body for law in dl.parse_laws(gen)}
    assert len(drafted) == 7

    # exact proposition match
    assert rows["unapproved_never_pass"]["match"] == "exact"  # weak independence: spec 4.1 has an example
    assert rows["agg_single_identity"]["match"] == "proposition"
    assert rows["agg_single_identity"]["generated_name"] == "aggregate_singleton"

    # same meaning, different form: Model.worse instead of Model.aggregate on a pair
    assert rows["agg_pair_commutes"]["match"] == "none"
    assert "Model.worse(a, b) == Model.worse(b, a)" in drafted["worse_commutative"]

    # judge(True, e, False) == 4n is covered by two narrower laws together
    assert rows["pass_requires_marker"]["match"] == "none"
    assert "Model.judge(True{}, False{}, m) == 4n" in drafted["approved_exit_failure_fails"]
    assert "Model.judge(True{}, True{}, False{}) == 4n" in drafted["approved_missing_marker_fails"]

    # not reproduced: the spec never states the result for empty input
    assert rows["agg_empty_skipped"]["match"] == "none"
    assert not any("Nil" in body for body in drafted.values())
    assert result["passed"] is False


def test_acceptance_draft_hash_is_stable():
    """Content hash reported by the independent run. The static check against the live
    spec is not asserted here: it would fail on any later edit of proof-gate_spec 3.1.1
    (that drift is what the ``source_drift`` warning is for)."""
    sys.path.insert(0, str(ROOT / "plugins/sdd-workflow/scripts"))
    from laws_header import law_body_hash
    gen, _, _ = _acceptance()
    assert law_body_hash(gen) == "2843fb9c5644"


def test_compare_detects_missing_law(tmp_path):
    gen = tmp_path / "g.bend"
    gen.write_text("law only:\n  {1n == 1n : Nat}\n")
    ref = tmp_path / "r.bend"
    ref.write_text("law other:\n  {2n == 2n : Nat}\n")
    result = dl.cmd_compare(type("N", (), {"generated": str(gen), "reference": str(ref)}))
    assert result["passed"] is False and result["results"][0]["match"] == "none"
