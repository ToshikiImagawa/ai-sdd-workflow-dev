"""laws_drafting.py のユニットテスト（pytest）。

節ハッシュ（laws-drafting_spec FR-003 / §4.1）、静的チェック（FR-006 / 3.1.3）、
出典ずれ判定（FR-011 / FR-013）、承認有効性判定（FR-007）を検証する。bend は不要。
"""

import hashlib
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "sdd-workflow" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load_module():
    spec = importlib.util.spec_from_file_location("laws_drafting", SCRIPTS / "laws_drafting.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ld = _load_module()
import laws_header as lh  # noqa: E402

SPEC = """---
id: "spec-demo"
title: "Demo"
---

# 1. 背景

intro

# 3. 要求定義

## 3.1. 機能要件

要件本文

### 3.1.1. 判定表（FR-002）

| a | b |
|:--|:--|
| 1 | 2 |

```
# 3.9. not a heading
```

### 3.1.2 上限

上限本文

## 3.2. 非機能要件

nfr

# 4. 提供コンポーネント

comp
"""


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- section extraction / hash --------------------------------------------


def test_find_section_includes_children_until_same_or_higher_level():
    body = ld.find_section(SPEC, "3.1")
    assert "要件本文" in body and "判定表" not in body.splitlines()[0]
    assert "上限本文" in body            # child 3.1.2 included
    assert "nfr" not in body             # next same-level (3.2) excluded


def test_find_section_leaf_stops_at_next_sibling_and_ignores_fenced_heading():
    body = ld.find_section(SPEC, "3.1.1")
    assert "| 1 | 2 |" in body
    assert "# 3.9. not a heading" in body  # fenced '#' is content
    assert "上限本文" not in body


def test_find_section_number_forms_and_misses():
    assert ld.find_section(SPEC, "3.1.2") == "\n上限本文\n"  # heading without trailing period
    assert ld.find_section(SPEC, "§3.1.1.") is not None      # § and trailing period tolerated
    assert ld.find_section(SPEC, "3.9") is None              # only inside a fence
    assert ld.find_section(SPEC, "11") is None               # '1' / '11' never prefix-match
    assert ld.find_section(SPEC, "") is None


def test_unnumbered_heading_is_not_a_source_target():
    text = "# Overview\n\nbody\n\n# 2. Next\n\nx\n"
    assert ld.find_section(text, "1") is None
    assert ld.find_section(text, "2") == "\nx"


def test_front_matter_is_not_scanned_for_headings():
    text = "---\nid: x\n# 1. fake\n---\n\n# 1. real\n\nbody\n"
    assert ld.find_section(text, "1") == "\nbody"


def test_normalize_section_rules():
    assert ld.normalize_section("\n\n a  \r\n\r\n\r\n\r\n b \t\n\n") == "a\n\nb"
    # inner whitespace is preserved
    assert ld.normalize_section("a  b") == "a  b"


def test_section_hash_matches_normalised_sha256_and_is_stable_under_whitespace():
    h = ld.section_hash(SPEC, "3.1.2")
    assert h == _digest("上限本文")
    noisy = SPEC.replace("上限本文", "   上限本文   \r\n\r\n\r\n").replace("\n", "\r\n")
    assert ld.section_hash(noisy, "3.1.2") == h
    assert ld.section_hash(SPEC.replace("上限本文", "上限本文2"), "3.1.2") != h
    assert ld.section_hash(SPEC, "9.9") is None


def test_section_hash_changes_when_child_changes():
    assert ld.section_hash(SPEC, "3.1") != ld.section_hash(SPEC.replace("上限本文", "x"), "3.1")


def test_section_hash_of_file_and_spec_id(tmp_path):
    p = _write(tmp_path / "spec.md", SPEC)
    assert ld.section_hash_of_file(p, "3.1.2") == _digest("上限本文")
    assert ld.spec_id_of(SPEC) == "spec-demo"
    assert ld.spec_id_of("# no fm\n") == ""


# --- source parsing / law parsing -----------------------------------------


def test_parse_source():
    ref = ld.parse_source("spec-demo §3.1.1 sha256:0123456789ab")
    assert ref == ("spec-demo", "3.1.1", "0123456789ab")
    for bad in ("spec-demo 3.1.1 sha256:0123456789ab", "spec-demo §3.1.1 sha256:XYZ",
                "spec-demo §3.1.1", "§3.1.1 sha256:0123456789ab", "spec-demo §3.1.1 sha256:0123456789abc"):
        assert ld.parse_source(bad) is None


def _laws(hash_a="0" * 12, extra=""):
    return (
        "# spec: spec-demo\n#\n# header\n\n"
        "import Base\nimport ./main.bend as Model\n\n"
        "# model-api: Model.judge(a: Bool) -> Nat  # PASS=0\n\n"
        f"# source: spec-demo §3.1.2 sha256:{hash_a}\n"
        "law one:\n  for a: Bool\n  {Model.judge(a) == 1n : Nat}\n"
        f"{extra}"
    )


def test_parse_laws_attaches_nearest_source_and_body(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    extra = "\nlaw two:\n  {Model.judge(True{}) == 4n : Nat}\n"
    p = _write(tmp_path / "LAWS.bend", _laws(h, extra))
    one, two = ld.parse_laws(p)
    assert (one.name, one.source) == ("one", ("spec-demo", "3.1.2", h))
    assert two.name == "two" and two.source_raw is None  # code line stops the upward search
    assert one.body == "for a: Bool {Model.judge(a) == 1n : Nat}"
    assert one.line < two.line


def test_model_api_functions_only_reads_body(tmp_path):
    p = _write(tmp_path / "LAWS.bend", _laws())
    assert ld.model_api_functions(p) == ["judge"]
    header_only = _write(
        tmp_path / "h" / "LAWS.bend",
        "# model-api: Model.judge(a: Bool) -> Nat\n\nimport Base\n\nlaw x:\n  {1n == 1n : Nat}\n")
    assert ld.model_api_functions(header_only) is None
    assert ld.model_api_functions(_write(tmp_path / "n" / "LAWS.bend", "import Base\n")) is None


# --- source drift (FR-011 / FR-013) ----------------------------------------


def test_source_drift_none_when_in_sync_and_for_handwritten_laws(tmp_path):
    spec = _write(tmp_path / "spec.md", SPEC)
    ok = _write(tmp_path / "a" / "LAWS.bend", _laws(ld.section_hash(SPEC, "3.1.2")))
    assert ld.source_drift(ok, spec) == []
    hand = _write(tmp_path / "b" / "LAWS.bend", "import Base\n\nlaw h:\n  {1n == 1n : Nat}\n")
    assert ld.source_drift(hand, spec) == []


def test_source_drift_reports_changed_missing_and_invalid(tmp_path):
    spec = _write(tmp_path / "spec.md", SPEC)
    stale = _write(tmp_path / "a" / "LAWS.bend", _laws("f" * 12))
    assert ld.source_drift(stale, spec) == [
        {"code": "source_drift", "law": "one", "source": "3.1.2"}]
    gone = _write(tmp_path / "b" / "LAWS.bend",
                  _laws("f" * 12).replace("§3.1.2", "§7.7"))
    assert ld.source_drift(gone, spec) == [
        {"code": "source_drift", "law": "one", "source": "7.7"}]
    bad = _write(tmp_path / "c" / "LAWS.bend",
                 _laws().replace("spec-demo §3.1.2 sha256:" + "0" * 12, "garbage"))
    assert ld.source_drift(bad, spec) == [
        {"code": "source_invalid", "law": "one", "source": "garbage"}]


def test_source_drift_flags_other_spec_id(tmp_path):
    spec = _write(tmp_path / "spec.md", SPEC)
    p = _write(tmp_path / "LAWS.bend",
               _laws(ld.section_hash(SPEC, "3.1.2")).replace("# source: spec-demo", "# source: spec-other"))
    assert ld.source_drift(p, spec)[0]["code"] == "source_drift"


# --- static check ----------------------------------------------------------


def _codes(findings):
    return sorted((f.code, f.severity) for f in findings)


def test_static_check_clean_draft(tmp_path):
    spec = _write(tmp_path / "spec.md", SPEC)
    p = _write(tmp_path / "LAWS.bend", _laws(ld.section_hash(SPEC, "3.1.2")))
    assert ld.static_check(p, spec) == []
    assert not ld.has_errors([])


def test_static_check_source_errors(tmp_path):
    spec = _write(tmp_path / "spec.md", SPEC)
    h = ld.section_hash(SPEC, "3.1.2")
    # hash mismatch -> error at draft time
    p = _write(tmp_path / "a" / "LAWS.bend", _laws("f" * 12))
    assert _codes(ld.static_check(p, spec)) == [("source_drift", "error")]
    # missing section
    p = _write(tmp_path / "b" / "LAWS.bend", _laws(h).replace("§3.1.2", "§8"))
    assert _codes(ld.static_check(p, spec)) == [("source_section_missing", "error")]
    # missing source (draft output must have one)
    p = _write(tmp_path / "c" / "LAWS.bend",
               _laws(h).replace(f"# source: spec-demo §3.1.2 sha256:{h}\n", ""))
    f = ld.static_check(p, spec)
    assert _codes(f) == [("source_missing", "error")] and ld.has_errors(f)
    # source checks are skipped without a spec, the missing-source check is not
    assert _codes(ld.static_check(p)) == [("source_missing", "error")]
    assert ld.static_check(_write(tmp_path / "d" / "LAWS.bend", _laws("f" * 12))) == []


def test_static_check_duplicate_and_trivial_are_warnings(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    extra = (f"\n# source: spec-demo §3.1.2 sha256:{h}\nlaw dup:\n  for a: Bool\n"
             "  {Model.judge(a) == 1n : Nat}\n"
             f"\n# source: spec-demo §3.1.2 sha256:{h}\nlaw same:\n  for a: Bool\n"
             "  {Model.judge( a ) == Model.judge(a)  : Nat}\n")
    p = _write(tmp_path / "LAWS.bend", _laws(h, extra))
    spec = _write(tmp_path / "spec.md", SPEC)
    f = ld.static_check(p, spec)
    assert _codes(f) == [("duplicate_law", "warning"), ("trivial_law", "warning")]
    assert next(x for x in f if x.code == "duplicate_law").law == "dup"
    assert not ld.has_errors(f)


def test_trivial_detection_ignores_nonidentical_and_nested_braces(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    p = _write(tmp_path / "LAWS.bend", _laws(h).replace(
        "{Model.judge(a) == 1n : Nat}", "{Model.judge(False{}) == Model.judge(a) : Nat}"))
    assert ld.static_check(p, _write(tmp_path / "spec.md", SPEC)) == []


def test_static_check_imports(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    spec = _write(tmp_path / "spec.md", SPEC)
    # ./main.bend may be absent at draft time, any other local import must exist
    p = _write(tmp_path / "LAWS.bend", _laws(h).replace("import Base\n", "import Base\nimport ./other.bend as O\n"))
    f = ld.static_check(p, spec)
    assert [(x.code, x.severity) for x in f] == [("import_disallowed", "error")]
    assert "other.bend" in f[0].message
    p2 = _write(tmp_path / "x" / "LAWS.bend", _laws(h).replace("import Base\n", "import Base\nfrom a import b\n"))
    assert _codes(ld.static_check(p2, _write(tmp_path / "spec.md", SPEC))) == [("import_disallowed", "error")]
    # strict mode: main.bend must exist
    assert _codes(ld.static_check(p, spec, tolerate_missing_model=False)) == [
        ("import_disallowed", "error"), ("import_disallowed", "error")]
    _write(tmp_path / "other.bend", "")
    _write(tmp_path / "main.bend", "")
    assert ld.static_check(p, spec, tolerate_missing_model=False) == []


def test_static_check_model_api(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    spec = _write(tmp_path / "spec.md", SPEC)
    no_api = _laws(h).replace("# model-api: Model.judge(a: Bool) -> Nat  # PASS=0\n", "")
    assert _codes(ld.static_check(_write(tmp_path / "a" / "LAWS.bend", no_api), spec)) == [
        ("model_api_missing", "error")]
    # api line only in the unhashed header is as good as missing, and says so
    hdr = no_api.replace("# header\n", "# header\n# model-api: Model.judge(a: Bool) -> Nat\n")
    f = ld.static_check(_write(tmp_path / "b" / "LAWS.bend", hdr), spec)
    assert _codes(f) == [("model_api_missing", "error")] and "header" in f[0].message
    # referenced but undeclared / declared but unused
    wrong = _laws(h).replace("Model.judge(a: Bool)", "Model.other(a: Bool)")
    f = ld.static_check(_write(tmp_path / "c" / "LAWS.bend", wrong), spec)
    assert [x.code for x in f] == ["model_api_mismatch", "model_api_mismatch"]
    assert ld.has_errors(f)
    # no Model.* use and no api line: nothing to check
    plain = ("# spec: spec-demo\n\nimport Base\n\n"
             f"# source: spec-demo §3.1.2 sha256:{h}\nlaw p:\n  for a: Nat\n  {{a + 0n == a : Nat}}\n")
    assert ld.static_check(_write(tmp_path / "d" / "LAWS.bend", plain), spec) == []


def test_model_api_check_ignores_comment_lines_in_law(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    p = _write(tmp_path / "LAWS.bend", _laws(h).replace(
        "  for a: Bool\n", "  # see Model.ghost for background\n  for a: Bool\n"))
    assert ld.static_check(p, _write(tmp_path / "spec.md", SPEC)) == []
    assert "ghost" not in ld.parse_laws(p)[0].body


def test_public_header_helpers(tmp_path):
    p = _write(tmp_path / "LAWS.bend", "# a\n\nimport Base\n")
    lines = lh.read_lines(p)
    assert lh.header_end(lines) == 2 and lines[2] == "import Base"


def test_static_check_applies_to_draft_file_name_too(tmp_path):
    spec = _write(tmp_path / "spec.md", SPEC)
    p = _write(tmp_path / "LAWS.draft.bend", _laws("f" * 12))
    assert _codes(ld.static_check(p, spec)) == [("source_drift", "error")]


# --- approval status -------------------------------------------------------


def _approved_file(tmp_path, approval_for=None, line=None):
    body = "import Base\n\nlaw a:\n  {1n == 1n : Nat}\n"
    digest = _digest("\n".join(body.splitlines()))
    value = line if line is not None else f"# approved: 2026-10-19 @me sha256:{approval_for or digest}\n"
    return _write(tmp_path / "LAWS.bend", f"# spec: x\n{value}\n{body}"), digest


def test_approval_status_states(tmp_path):
    missing = _write(tmp_path / "m" / "LAWS.bend", "# spec: x\n\nimport Base\n\nlaw a:\n  {1n == 1n : Nat}\n")
    st = ld.approval_status(missing)
    assert st.state == "missing" and st.approval is None and len(st.current_hash) == 12

    p, digest = _approved_file(tmp_path / "v")
    st = ld.approval_status(p)
    assert st == ("valid", digest, f"2026-10-19 @me sha256:{digest}")

    p, digest = _approved_file(tmp_path / "x", approval_for="0" * 12)
    st = ld.approval_status(p)
    assert st.state == "mismatch" and st.current_hash == digest and st.approval.endswith("0" * 12)

    for bad in ("# approved: yesterday me sha256:abc\n",
                "# approved: 2026-13-45 @me sha256:" + "0" * 12 + "\n"):
        p, _ = _approved_file(tmp_path / ("b" + str(hash(bad))), line=bad)
        assert ld.approval_status(p).state == "malformed"

    assert ld.approval_status(tmp_path / "nope.bend") == ("no_file", "", None)


def test_approval_status_agrees_with_laws_header(tmp_path):
    p, digest = _approved_file(tmp_path)
    assert digest == lh.law_body_hash(p)
    assert lh.valid_approval(lh.read_header(p), digest) == ld.approval_status(p).approval
    p.write_text(p.read_text(encoding="utf-8") + "# more\n", encoding="utf-8")
    assert ld.approval_status(p).state == "mismatch"  # editing the body expires approval


def test_laws_header_file_disallowed_imports_matches_directory_scan(tmp_path):
    _write(tmp_path / "LAWS.bend", "import Base\nimport ./gone.bend as G\nfrom a import b\n")
    assert lh.file_disallowed_imports(tmp_path / "LAWS.bend", tmp_path.resolve()) == [
        "import ./gone.bend as G", "from a import b"]
    assert lh.file_disallowed_imports(
        tmp_path / "LAWS.bend", tmp_path.resolve(), ["./gone.bend"]) == ["from a import b"]
    assert lh.disallowed_imports(tmp_path) == [
        "LAWS.bend: import ./gone.bend as G", "LAWS.bend: from a import b"]


def test_unbounded_nat_literal_warning(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    spec = _write(tmp_path / "spec.md", SPEC)

    def laws(body):
        return ("# spec: spec-demo\n\nimport Base\nimport ./main.bend as Model\n\n"
                "# model-api: Model.f(a: Nat) -> Nat\n"
                f"# source: spec-demo §3.1.2 sha256:{h}\nlaw l:\n{body}")
    bad = _write(tmp_path / "a" / "LAWS.bend", laws("  for a: Nat\n  {Model.f(a) == 4n : Nat}\n"))
    assert [(f.code, f.severity) for f in ld.static_check(bad, spec)] == [("unbounded_nat_literal", "warning")]
    # literal on the left, and a literal argument with a Nat variable
    bad2 = _write(tmp_path / "b" / "LAWS.bend", laws("  for a: Nat\n  {4n == Model.f(4n, a) : Nat}\n"))
    assert [f.code for f in ld.static_check(bad2, spec)] == ["unbounded_nat_literal"]
    # no Nat variable in the call (Bool only) or no literal side: no warning
    ok = _write(tmp_path / "c" / "LAWS.bend", laws("  for a: Nat\n  {Model.f(a) == Model.f(a + 0n) : Nat}\n"))
    assert ld.static_check(ok, spec) == []
    ok2 = _write(tmp_path / "d" / "LAWS.bend", laws("  for e: Bool\n  {Model.f(e) == 4n : Nat}\n"))
    assert ld.static_check(ok2, spec) == []


def test_fixed_model_api_priority_and_check(tmp_path):
    h = ld.section_hash(SPEC, "3.1.2")
    spec_text = SPEC + "\nmodel-api: Model.judge(a: Bool) -> Nat\n"
    spec = _write(tmp_path / "spec.md", spec_text)
    d = tmp_path / "laws"
    assert ld.fixed_model_api(SPEC, d)[0] == "unfixed"
    _write(d / "main.bend", "def other(x: Nat) -> Nat:\n  return x\n\ndef main() -> Nat:\n  return 0n\n")
    assert ld.fixed_model_api(SPEC, d) == ("main.bend", {"other": "Model.other(x: Nat) -> Nat"})
    assert ld.fixed_model_api(spec_text, d)[0] == "spec"  # spec declaration wins
    # `# model-api:` in a law file is not a spec declaration
    assert ld.model_api_from_spec("# model-api: Model.x() -> Nat\n") == {}
    f = ld.static_check(_write(d / "LAWS.bend", _laws(h)), spec)
    assert f == []  # Model.judge is in the spec-fixed API
    f = ld.static_check(_write(d / "LAWS.bend", _laws(h)), _write(tmp_path / "s2.md", SPEC))
    assert {x.code for x in f} == {"model_api_not_fixed"}  # main.bend fixes only `other`
