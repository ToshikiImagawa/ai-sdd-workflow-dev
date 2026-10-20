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


def _ns(gen, ref, judgement="", check_result=""):
    return type("N", (), {"generated": str(gen), "reference": str(ref), "judgement": str(judgement), "model": "",
                          "check_result": str(check_result)})


def _acceptance():
    gen = FIXTURES / "proof-gate-acceptance.LAWS.draft.bend"
    result = dl.cmd_compare(_ns(gen, REFERENCE))
    return gen, {r["law"]: r for r in result["results"]}, result


def test_acceptance_independent_reproduction_correspondence():
    """laws-drafting_spec §11 (sixth independent re-run, head 158e5f7: 10 laws, content hash 97d5dbf04b24).

    Stage 1 (mechanical, ``compare`` with alpha equivalence and ``rank_*`` constants read from
    main.bend): all 5 first-wave laws match, ``agg_pair_commutes`` included because the run wrote
    the commutativity on ``aggregate`` (aggregate-first rule, #180). No stage 2 judgement is needed.
    """
    gen, rows, result = _acceptance()
    assert len(dl.parse_laws(gen)) == 10
    assert {k: v["match"] for k, v in rows.items()} == {
        "agg_empty_skipped": "proposition", "agg_single_identity": "proposition",
        "agg_pair_commutes": "proposition", "unapproved_never_pass": "proposition",
        "pass_requires_marker": "proposition"}
    assert rows["agg_pair_commutes"]["generated_name"] == "aggregate_commutative"
    assert result["passed_mechanical"] is True and result["passed"] is True
    assert result["pending_judgement"] == []


def test_acceptance_draft_hash_is_stable():
    """Content hash reported by the independent run. The static check against the live
    spec is not asserted here: it would fail on any later edit of proof-gate_spec 3.1.1
    (that drift is what the ``source_drift`` warning is for)."""
    sys.path.insert(0, str(ROOT / "plugins/sdd-workflow/scripts"))
    from laws_header import law_body_hash
    gen, _, _ = _acceptance()
    assert law_body_hash(gen) == "97d5dbf04b24"


def test_compare_detects_missing_law(tmp_path):
    gen = tmp_path / "g.bend"
    gen.write_text("law only:\n  {1n == 1n : Nat}\n")
    ref = tmp_path / "r.bend"
    ref.write_text("law other:\n  {2n == 2n : Nat}\n")
    result = dl.cmd_compare(_ns(gen, ref))
    assert result["passed"] is False and result["results"][0]["match"] == "none"


def _judge(tmp_path, judgements):
    """Compare the acceptance fixture minus its ``aggregate_commutative`` law (a stage 1 miss)."""
    text = (FIXTURES / "proof-gate-acceptance.LAWS.draft.bend").read_text()
    start = text.rindex("# source:", 0, text.index("law aggregate_commutative:"))
    end = text.index("# source:", text.index("law aggregate_commutative:"))
    gen = tmp_path / "g.bend"
    gen.write_text(text[:start] + text[end:])
    f = tmp_path / "j.json"
    f.write_text(json.dumps(judgements))
    return dl.cmd_compare(_ns(gen, REFERENCE, f))


def test_compare_second_stage_human_judgement(tmp_path):
    """spec §11 stage 2: ``weak`` fails, ``equivalent`` passes; stage 1 stays False."""
    weak = _judge(tmp_path, {"agg_pair_commutes": "weak"})
    assert weak["passed"] is False and weak["passed_mechanical"] is False
    assert weak["pending_judgement"] == []
    ok = _judge(tmp_path, {"agg_pair_commutes": "equivalent"})
    assert ok["passed"] is True and ok["passed_mechanical"] is False


def test_compare_rejects_unknown_judgement(tmp_path):
    with pytest.raises(SystemExit):
        _judge(tmp_path, {"agg_empty_skipped": "maybe"})


def test_acceptance_fixture_check_against_fixed_api():
    """The 6th run uses only functions of the fixed API (main.bend beside the reference laws):
    no error and no warning."""
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(FIXTURES / "proof-gate-acceptance.LAWS.draft.bend", Path(d) / "LAWS.draft.bend")
        shutil.copy(REFERENCE.parent / "main.bend", Path(d) / "main.bend")
        out = dl.cmd_check(type("N", (), {"laws_file": str(Path(d) / "LAWS.draft.bend"), "spec": "",
                                          "require_model": False, "feature": "", "project_root": ""}))
    assert out["findings"] == [] and out["propose_drafted"] is True
    assert out["model_api"]["fixed"] is True


def test_model_api_subcommand_priority(tmp_path):
    root = tmp_path
    (root / ".sdd/specification").mkdir(parents=True)
    (root / ".sdd/specification/demo_spec.md").write_text(SPEC_TEXT)
    out = dl.cmd_model_api(type("N", (), {"feature": "demo", "project_root": str(root)}))
    assert out["source"] == "unfixed" and out["fixed"] is False
    laws = root / ".sdd/laws/demo"
    laws.mkdir(parents=True)
    (laws / "main.bend").write_text("def judge(a: Bool) -> Nat:\n  return 1n\n\ndef main() -> Nat:\n  return 0n\n")
    out = dl.cmd_model_api(type("N", (), {"feature": "demo", "project_root": str(root)}))
    assert out["source"] == "main.bend" and [f["name"] for f in out["functions"]] == ["Model.judge"]
    (root / ".sdd/specification/demo_spec.md").write_text(SPEC_TEXT + "\nmodel-api: Model.rank(x: Nat) -> Nat\n")
    out = dl.cmd_model_api(type("N", (), {"feature": "demo", "project_root": str(root)}))
    assert out["source"] == "spec" and [f["name"] for f in out["functions"]] == ["Model.rank"]


GEN = "law a:\n  {1n == 1n : Nat}\n\nlaw b:\n  {Model.f(True{}) == 2n : Nat}\n"
REF = "law a:\n  {1n == 1n : Nat}\n\nlaw c:\n  {Model.g(True{}) == 3n : Nat}\n"


def _files(tmp_path, gen=GEN, ref=REF):
    (tmp_path / "g.bend").write_text(gen)
    (tmp_path / "r.bend").write_text(ref)
    return tmp_path / "g.bend", tmp_path / "r.bend"


def _json(tmp_path, name, data):
    f = tmp_path / name
    f.write_text(data if isinstance(data, str) else json.dumps(data))
    return f


def test_compare_empty_reference_never_passes(tmp_path):
    gen, ref = _files(tmp_path, ref="# no laws\n")
    result = dl.cmd_compare(_ns(gen, ref))
    assert result["passed"] is False and result["passed_mechanical"] is False and "error" in result
    r = subprocess.run([sys.executable, str(SCRIPT), "compare", str(gen), str(ref)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and json.loads(r.stdout)["passed"] is False


def test_compare_judgement_cases(tmp_path):
    gen, ref = _files(tmp_path)
    # none -> fail; unjudged -> pending; partial judgement on a matched law is ignored
    none = dl.cmd_compare(_ns(gen, ref, _json(tmp_path, "j.json", {"c": "none"})))
    assert none["passed"] is False and none["pending_judgement"] == []
    pending = dl.cmd_compare(_ns(gen, ref))
    assert pending["passed"] is False and pending["pending_judgement"] == ["c"]
    ok = dl.cmd_compare(_ns(gen, ref, _json(tmp_path, "k.json", {"c": "equivalent", "a": "none", "zzz": "weak"})))
    assert ok["passed"] is True and ok["ignored_judgements"] == ["a"] and ok["unknown_judgements"] == ["zzz"]
    # object form (R7)
    obj = dl.cmd_compare(_ns(gen, ref, _json(tmp_path, "o.json", {
        "c": {"verdict": "equivalent", "generated_name": "b", "note": "same meaning"}})))
    row = [r for r in obj["results"] if r["law"] == "c"][0]
    assert obj["passed"] is True and row["judged_generated_name"] == "b" and row["judgement_note"] == "same meaning"


@pytest.mark.parametrize("content", ["{not json", "[1, 2]", '{"c": "maybe"}', '{"c": {"note": "x"}}'])
def test_compare_judgement_input_is_validated(tmp_path, content):
    gen, ref = _files(tmp_path)
    j = _json(tmp_path, "bad.json", content)
    r = subprocess.run([sys.executable, str(SCRIPT), "compare", str(gen), str(ref), "--judgement", str(j)],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "Traceback" not in r.stderr


def test_compare_check_errors_block_pass(tmp_path):
    gen, ref = _files(tmp_path)
    j = _json(tmp_path, "j.json", {"c": "equivalent"})
    clean = _json(tmp_path, "c0.json", {"errors": 0})
    dirty = _json(tmp_path, "c1.json", {"errors": 2})
    assert dl.cmd_compare(_ns(gen, ref, j, clean))["passed"] is True
    out = dl.cmd_compare(_ns(gen, ref, j, dirty))
    assert out["passed"] is False and out["check_errors"] == 2


def test_compare_cli_with_judgement_and_check_result(tmp_path):
    gen, ref = _files(tmp_path)
    j = _json(tmp_path, "j.json", {"c": "equivalent"})
    c = _json(tmp_path, "c.json", {"errors": 0})
    code, out = run("compare", str(gen), str(ref), "--judgement", str(j), "--check-result", str(c))
    assert code == 0 and out["passed"] is True and out["passed_mechanical"] is False


def test_rank_unbounded_flag():
    out = dl.rank_candidates([{"name": "x", "section": "1", "priority": 1, "body": "b", "unbounded": True}], 5)
    assert out["adopted"] == [] and out["not_adopted"][0]["reason"] == "unbounded_nat"


def test_model_api_unreadable_main_bend(tmp_path):
    (tmp_path / ".sdd/specification").mkdir(parents=True)
    (tmp_path / ".sdd/specification/demo_spec.md").write_text(SPEC_TEXT)
    laws = tmp_path / ".sdd/laws/demo"
    laws.mkdir(parents=True)
    (laws / "main.bend").write_text("# a model with no recognisable def\nsome garbage\n")
    out = dl.cmd_model_api(type("N", (), {"feature": "demo", "project_root": str(tmp_path)}))
    assert out["source"] == "main.bend-unreadable" and out["fixed"] is False and "warning" in out


def test_check_feature_resolves_fixed_api_for_file_outside_laws_dir(tmp_path):
    root = tmp_path / "proj"
    (root / ".sdd/specification").mkdir(parents=True)
    (root / ".sdd/specification/demo_spec.md").write_text(SPEC_TEXT)
    laws_dir = root / ".sdd/laws/demo"
    laws_dir.mkdir(parents=True)
    (laws_dir / "main.bend").write_text("def judge(a: Bool) -> Nat:\n  return 1n\n")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    draft = scratch / "LAWS.draft.bend"
    draft.write_text("# spec: spec-demo\n\nimport Base\nimport ./main.bend as Model\n\n"
                     "# model-api: Model.extra(a: Bool) -> Nat\n"
                     "# source: spec-demo §2.1 sha256:000000000000\n"
                     "law l:\n  for a: Bool\n  {Model.extra(a) == 1n : Nat}\n")
    # without --feature the API is unfixed and the check is silent, but the result says so
    code, plain = run("check", str(draft))
    assert plain["model_api"]["source"] == "unfixed" and "notes" in plain
    assert "model_api_not_fixed" not in {f["code"] for f in plain["findings"]}
    # with --feature the fixed API (main.bend of the feature) is applied
    code, out = run("check", str(draft), "--feature", "demo", "--project-root", str(root))
    assert out["model_api"] == {"source": "main.bend", "fixed": True, "functions": ["judge"]}
    assert "notes" not in out
    assert "model_api_not_fixed" in {f["code"] for f in out["findings"]}
    assert out["propose_drafted"] is False


def test_rank_takes_basic_properties_first_within_a_priority():
    cands = [
        {"name": "a_narrow", "section": "3.1.1", "priority": 2, "body": "1"},
        {"name": "b_commutes", "section": "3.1.1", "priority": 2, "kind": "commutative", "body": "2"},
        {"name": "c_empty", "section": "3.1.1", "priority": 2, "kind": "empty", "body": "3"},
        {"name": "z_first_prio", "section": "9", "priority": 1, "body": "4"},
    ]
    out = dl.rank_candidates(cands, 3)
    assert [c["name"] for c in out["adopted"]] == ["z_first_prio", "b_commutes", "c_empty"]
    assert [c["name"] for c in out["not_adopted"]] == ["a_narrow"]


def test_rank_puts_binary_level_properties_after_aggregate_ones():
    cands = [
        {"name": "a_worse_commutes", "section": "3.1.1", "priority": 2, "kind": "commutative", "level": "binary", "body": "1"},
        {"name": "b_narrow", "section": "3.1.1", "priority": 2, "body": "2"},
        {"name": "c_agg_pair_commutes", "section": "3.1.1", "priority": 2, "kind": "commutative", "body": "3"},
    ]
    out = dl.rank_candidates(cands, 2)
    assert [c["name"] for c in out["adopted"]] == ["c_agg_pair_commutes", "b_narrow"]
    assert [(c["name"], c["reason"]) for c in out["not_adopted"]] == [("a_worse_commutes", "limit")]
    assert [c["name"] for c in dl.rank_candidates(cands, 3)["adopted"]][-1] == "a_worse_commutes"


def test_rank_level_without_kind_goes_last_and_other_level_values_are_ignored():
    cands = [
        {"name": "a_bin", "section": "1", "priority": 2, "level": "binary", "body": "1"},
        {"name": "b_plain", "section": "1", "priority": 2, "body": "2"},
        {"name": "c_other_level", "section": "1", "priority": 2, "level": "aggregate", "body": "3"},
    ]
    assert [c["name"] for c in dl.rank_candidates(cands, 3)["adopted"]] == ["b_plain", "c_other_level", "a_bin"]


def test_rank_level_does_not_override_priority():
    cands = [
        {"name": "agg", "section": "1", "priority": 2, "kind": "commutative", "body": "1"},
        {"name": "bin_p1", "section": "1", "priority": 1, "level": "binary", "body": "2"},
    ]
    assert [c["name"] for c in dl.rank_candidates(cands, 2)["adopted"]] == ["bin_p1", "agg"]


def test_rank_without_aggregate_function_is_unchanged_by_level_absence():
    cands = [
        {"name": "b", "section": "2", "priority": 2, "kind": "empty", "body": "1"},
        {"name": "a", "section": "1", "priority": 2, "kind": "commutative", "body": "2"},
        {"name": "z", "section": "0", "priority": 2, "body": "3"},
    ]
    assert [c["name"] for c in dl.rank_candidates(cands, 3)["adopted"]] == ["a", "b", "z"]


def test_normalise_proposition_alpha_constants_and_nil():
    consts = {"rank_fail": "4n", "rank_pass": "0n"}
    n = dl.normalise_proposition
    # alpha equivalence: only the declared variables are renamed (not Model.x, not other words)
    assert n("for x: Nat {Model.aggregate([x]) == x : Nat}", consts) == \
        n("for a: Nat {Model.aggregate([a]) == a : Nat}", consts)
    assert n("for a: Nat for b: Nat {Model.f(a, b) == a : Nat}", consts) != \
        n("for a: Nat for b: Nat {Model.f(a, b) == b : Nat}", consts)
    assert n("for a, b: Nat {Model.f(a) == b : Nat}", consts) == n("for p, q: Nat {Model.f(p) == q : Nat}", consts)
    # constants and empty list
    assert n("{Model.judge(True{}) == Model.rank_fail() : Nat}", consts) == n("{Model.judge(True{}) == 4n : Nat}", consts)
    assert n("{Model.aggregate([]) == 1n : Nat}", consts) == n("{Model.aggregate(Nil{}) == 1n : Nat}", consts)
    # a different constant is not equal
    assert n("{Model.f() == Model.rank_pass() : Nat}", consts) != n("{Model.f() == Model.rank_fail() : Nat}", consts)


def test_compare_alpha_and_rank_constants(tmp_path):
    (tmp_path / "main.bend").write_text("def rank_fail() -> Nat:\n  4n\n\ndef main() -> Nat:\n  0n\n")
    gen = tmp_path / "g.bend"
    gen.write_text("law g1:\n  for e: Bool\n  {Model.judge(True{}, e, False{}) == Model.rank_fail() : Nat}\n")
    ref = tmp_path / "r.bend"
    ref.write_text("law r1:\n  for m: Bool\n  {Model.judge(True{}, m, False{}) == 4n : Nat}\n")
    out = dl.cmd_compare(_ns(gen, ref))
    assert out["passed"] is True and out["passed_mechanical"] is True
    assert out["results"][0]["match"] == "proposition"
    # without the model the constant stays a call: no match
    (tmp_path / "main.bend").unlink()
    assert dl.cmd_compare(_ns(gen, ref))["passed"] is False


def test_fourth_reproduction_stage_two_judgement_fails(tmp_path):
    """Owner decision: 4 of the 5 first-wave laws are equivalent / matched, agg_pair_commutes
    has no counterpart (none) -> not passed. Uses a trimmed copy of the 4th run's laws."""
    gen = tmp_path / "g.bend"
    gen.write_text(
        "law unapproved_never_pass:\n  for e: Bool\n  for m: Bool\n"
        "  {Model.judge(False{}, e, m) == Model.rank_skipped() : Nat}\n\n"
        "law aggregate_empty_skipped:\n  {Model.aggregate([]) == Model.rank_skipped() : Nat}\n\n"
        "law aggregate_singleton:\n  for a: Nat\n  {Model.aggregate([a]) == a : Nat}\n\n"
        "law missing_marker_is_fail:\n  for e: Bool\n  {Model.judge(True{}, e, False{}) == Model.rank_fail() : Nat}\n")
    out = dl.cmd_compare(_ns(gen, REFERENCE))
    rows = {r["law"]: r["match"] for r in out["results"]}
    assert rows == {"agg_empty_skipped": "proposition", "agg_single_identity": "proposition",
                    "agg_pair_commutes": "none", "unapproved_never_pass": "exact",
                    "pass_requires_marker": "proposition"}
    assert out["pending_judgement"] == ["agg_pair_commutes"] and out["passed"] is False
    j = _json(tmp_path, "j.json", {"agg_pair_commutes": "none"})
    final = dl.cmd_compare(_ns(gen, REFERENCE, j))
    assert final["passed"] is False and final["pending_judgement"] == []


def test_model_constants(tmp_path):
    ld = dl  # draft_laws imports model_constants from laws_drafting
    main = tmp_path / "main.bend"
    main.write_text("def rank_pass() -> Nat:\n  0n\n\ndef rank_x() -> Nat:\n  return 7n\n\n"
                    "def f(a: Nat) -> Nat:\n  1n\n")
    assert ld.model_constants(main) == {"rank_pass": "0n", "rank_x": "7n"}
