"""post-tool-use.py のユニットテスト（pytest）。

spec 探索、ファイルパス抽出、編集後ファイル種別ごとの
リマインダー emit 分岐を検証する。リファクタ前の安全網。
"""

import importlib.util
import os
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "post-tool-use.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("post_tool_use", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ptu = _load_module()

SPEC = os.path.join(".sdd", "specification")
PATHS = ptu.SddPaths()


def _process(rel_path: str, project_root) -> None:
    """Run the per-file hook logic against the default .sdd layout."""
    ptu._process_single_file(rel_path, str(project_root), PATHS)


# --- find_spec_doc ---------------------------------------------------------


class TestFindSpecDoc:
    def test_reexports_the_shared_implementation(self):
        # Behavior is covered by tests/test_doc_walker.py; assert only the wiring
        # so a future local reimplementation is caught here. A single combined
        # lookup is used (not find_spec_doc / find_legacy_design_doc
        # separately) so _process_source_file walks specification/ once per
        # source-file edit instead of up to three times.
        assert ptu.find_spec_or_legacy_design_doc.__module__ == "doc_walker"


# --- _extract_file_paths ---------------------------------------------------


class TestExtractFilePaths:
    def test_write_single_path(self):
        payload = {"tool_input": {"file_path": "a.py"}}
        assert ptu._extract_file_paths(payload) == ["a.py"]

    def test_multiedit_paths_deduped(self):
        payload = {"tool_input": {"edits": [
            {"file_path": "a.py"}, {"file_path": "b.py"}, {"file_path": "a.py"},
        ]}}
        assert ptu._extract_file_paths(payload) == ["a.py", "b.py"]

    def test_empty_payload(self):
        assert ptu._extract_file_paths({}) == []


# --- _process_single_file --------------------------------------------------


class TestProcessSingleFile:
    def test_specification_md_emits_consistency_reminder(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: None)
        _process(os.path.join(SPEC, "user-login_spec.md"), tmp_path)
        out = capsys.readouterr().out
        assert "PRD <-> spec <-> adr" in out
        assert "/constitution validate" in out

    def test_requirement_md_emits_propagation_reminder(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: None)
        _process(os.path.join(PATHS.requirement_prefix, "user-login.md"), tmp_path)
        out = capsys.readouterr().out
        assert "(PRD) was updated" in out
        assert "/constitution validate" in out

    def test_adr_md_emits_append_only_reminder(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: None)
        _process(os.path.join(PATHS.adr_prefix, "user-login.md"), tmp_path)
        out = capsys.readouterr().out
        assert "(ADR) was updated" in out
        assert "append-only" in out

    def test_adr_md_reindexes(self, tmp_path, monkeypatch):
        # adr/ is now an sdd_index target (issue #92), so editing it must
        # trigger the same reindex as specification/.
        calls = []
        monkeypatch.setattr(ptu, "try_update_index", lambda *a, **k: calls.append(a))
        _process(os.path.join(PATHS.adr_prefix, "user-login.md"), tmp_path)
        assert calls

    def test_other_sdd_file_no_output(self, tmp_path, capsys):
        _process(os.path.join(".sdd", "CONSTITUTION.md"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_task_dir_file_no_output(self, tmp_path, capsys):
        # task/ is temporary; the design draft there is not a sync target.
        _process(
            os.path.join(PATHS.task_prefix, "90", "design-draft.md"), tmp_path,
        )
        assert capsys.readouterr().out == ""

    def test_source_with_matching_spec_emits_sync_reminder(
        self, tmp_path, capsys
    ):
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app_spec.md").write_text("# s", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        out = capsys.readouterr().out
        assert "matching specification" in out
        assert "app_spec.md" in out
        assert "keep it as the source of truth" in out

    def test_source_with_suffixless_spec_emits_sync_reminder(
        self, tmp_path, capsys
    ):
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app.md").write_text("# s", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        assert "matching specification" in capsys.readouterr().out

    def test_source_with_only_design_doc_emits_adr_migration_reminder(
        self, tmp_path, capsys, monkeypatch
    ):
        # A v4.x design doc is not a spec, so the spec sync wording must not be
        # used; the reminder points at the adr/ migration instead.
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", "/plugins/sdd-workflow")
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app_design.md").write_text("# d", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        out = capsys.readouterr().out
        assert "v4.x design document" in out
        assert "app_design.md" in out
        assert PATHS.adr_prefix in out
        assert "Migration from v4.x" in out
        # The procedure pointer must be a path the agent can actually open,
        # plus the section name inside it.
        assert "/plugins/sdd-workflow/README.md" in out
        assert "Extracting Existing" in out
        # v4 assets are supplementary input, never a violation or deletion target.
        assert "supplementary input" in out
        assert "Keep the design doc until that is done" in out
        assert "matching specification" not in out

    def test_design_doc_reminder_falls_back_to_plugin_root_token(
        self, tmp_path, capsys, monkeypatch
    ):
        # Without CLAUDE_PLUGIN_ROOT in the process environment the reminder
        # still emits a token the session can resolve, never a bare "README".
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app_design.md").write_text("# d", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        assert "${CLAUDE_PLUGIN_ROOT}/README.md" in capsys.readouterr().out

    def test_spec_wins_over_legacy_design_doc(self, tmp_path, capsys):
        # When both exist the spec sync reminder is the only one emitted.
        spec_abs = tmp_path / SPEC
        spec_abs.mkdir(parents=True)
        (spec_abs / "app_spec.md").write_text("# s", encoding="utf-8")
        (spec_abs / "app_design.md").write_text("# d", encoding="utf-8")
        _process(os.path.join("src", "app.py"), tmp_path)
        out = capsys.readouterr().out
        assert "matching specification" in out
        assert "v4.x design document" not in out

    def test_source_without_spec_no_output(self, tmp_path, capsys):
        (tmp_path / SPEC).mkdir(parents=True)
        _process(os.path.join("src", "app.py"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_non_source_file_no_output(self, tmp_path, capsys):
        (tmp_path / SPEC).mkdir(parents=True)
        _process("notes.txt", tmp_path)
        assert capsys.readouterr().out == ""


# --- laws reminders (stale-doc-detection_spec FR-007 / FR-008) --------------


def _laws_project(tmp_path, model_of=("src/auth/user_login.py",)):
    d = tmp_path / ".sdd" / "laws" / "auth" / "user-login"
    d.mkdir(parents=True)
    (d / "LAWS.bend").write_text("# spec: spec-auth-user-login\n\nlaw a: 1\n", encoding="utf-8")
    lines = "".join(f"# model-of: {m}\n" for m in model_of)
    (d / "main.bend").write_text(f"# spec: spec-auth-user-login\n{lines}\nimport Base\n",
                                 encoding="utf-8")
    return d


class TestLawsReminders:
    def test_laws_bend_edit_reminds_rerun_and_reapproval(self, tmp_path, capsys):
        _laws_project(tmp_path)
        _process(os.path.join(".sdd", "laws", "auth", "user-login", "LAWS.bend"), tmp_path)
        out = capsys.readouterr().out
        assert "spec-auth-user-login" in out
        assert "/run-checklist auth/user-login" in out and "--category proof" in out
        assert "re-approval" in out

    def test_other_bend_edit_reminds_rerun_without_reapproval(self, tmp_path, capsys):
        _laws_project(tmp_path)
        _process(os.path.join(".sdd", "laws", "auth", "user-login", "PROOF.bend"), tmp_path)
        out = capsys.readouterr().out
        assert "--category proof" in out and "re-approval" not in out

    def test_bend_edit_without_laws_header_still_reminds(self, tmp_path, capsys):
        d = tmp_path / ".sdd" / "laws" / "x"
        d.mkdir(parents=True)
        (d / "PROOF.bend").write_text("import ./LAWS.bend as Laws\n", encoding="utf-8")
        _process(os.path.join(".sdd", "laws", "x", "PROOF.bend"), tmp_path)
        assert "--category proof" in capsys.readouterr().out

    def test_bend_outside_laws_dir_is_silent(self, tmp_path, capsys):
        _process(os.path.join("src", "x.bend"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_model_of_source_edit_reminds_review(self, tmp_path, capsys):
        _laws_project(tmp_path)
        _process(os.path.join("src", "auth", "user_login.py"), tmp_path)
        out = capsys.readouterr().out
        assert "main.bend" in out and "reference model" in out and "auth/user-login" in out

    def test_model_of_and_spec_sync_both_injected(self, tmp_path, capsys):
        _laws_project(tmp_path)
        spec = tmp_path / ".sdd" / "specification"
        spec.mkdir(parents=True)
        (spec / "user_login_spec.md").write_text("# spec\n", encoding="utf-8")
        _process(os.path.join("src", "auth", "user_login.py"), tmp_path)
        out = capsys.readouterr().out
        assert "matching specification" in out and "reference model" in out

    def test_non_matching_source_is_silent(self, tmp_path, capsys):
        _laws_project(tmp_path)
        _process(os.path.join("src", "other.py"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_no_laws_directory_is_silent(self, tmp_path, capsys):
        _process(os.path.join("src", "auth", "user_login.py"), tmp_path)
        assert capsys.readouterr().out == ""

    def test_bend_is_not_a_source_extension(self):
        assert ".bend" not in ptu.SOURCE_EXTENSIONS


# --- absolute / external .sdd root (issue #151) -----------------------------


class TestExternalSddRoot:
    """spec がプロジェクト外にあっても relative_to の ValueError で落とさない。"""

    def _external_layout(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        external = tmp_path / "external-sdd"
        (external / "specification").mkdir(parents=True)
        (external / "specification" / "foo_spec.md").write_text("# foo\n", encoding="utf-8")
        (proj / "foo.py").write_text("x = 1\n", encoding="utf-8")
        paths = ptu.SddPaths(root=str(external))
        return proj, external, paths

    def test_source_edit_with_external_spec_does_not_raise(self, tmp_path, capsys):
        proj, _external, paths = self._external_layout(tmp_path)
        ptu._process_single_file("foo.py", str(proj), paths)  # must not raise
        assert capsys.readouterr().out == ""

    def test_source_edit_with_external_legacy_design_does_not_raise(self, tmp_path, capsys):
        proj, external, paths = self._external_layout(tmp_path)
        (external / "specification" / "foo_spec.md").unlink()
        (external / "specification" / "foo_design.md").write_text("# d\n", encoding="utf-8")
        ptu._process_single_file("foo.py", str(proj), paths)
        assert capsys.readouterr().out == ""

    def test_main_exits_cleanly_for_external_root(self, tmp_path, monkeypatch, capsys):
        import io
        import json
        import sys

        proj, external, _paths = self._external_layout(tmp_path)
        (proj / ".sdd-config.json").write_text(
            json.dumps({"root": str(external)}), encoding="utf-8",
        )
        payload = {"cwd": str(proj), "tool_input": {"file_path": str(proj / "foo.py")}}
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        ptu.main()  # must not raise (previously ValueError -> rc=1)
        assert capsys.readouterr().out == ""


class TestModelOfOutsideProject:
    def test_absolute_laws_root_outside_project_is_silent(self, tmp_path, capsys):
        # #151: an absolute .sdd-config.json root points laws/ outside the project.
        project = tmp_path / "project"
        (project / "src" / "auth").mkdir(parents=True)
        external = tmp_path / "external-sdd"
        d = external / "laws" / "auth" / "user-login"
        d.mkdir(parents=True)
        (d / "main.bend").write_text(
            "# spec: spec-x\n# model-of: src/auth/user_login.py\n\nimport Base\n", encoding="utf-8")
        paths = ptu.SddPaths(root=str(external))
        ptu._process_model_of(Path("src/auth/user_login.py"), "src/auth/user_login.py",
                              str(project), paths)
        assert capsys.readouterr().out == ""


# --- spec edit -> laws re-draft reminder (laws-drafting_spec FR-011) -----------


def _spec_with_laws(tmp_path, source_hash):
    spec = tmp_path / ".sdd" / "specification" / "auth" / "user-login_spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text('---\nid: "spec-auth-user-login"\nlaws: ["laws/auth/user-login"]\n---\n'
                    "# 3. 要求\n\n## 3.1. 機能\n\n本文\n", encoding="utf-8")
    d = tmp_path / ".sdd" / "laws" / "auth" / "user-login"
    d.mkdir(parents=True)
    (d / "LAWS.bend").write_text(
        f"# spec: spec-auth-user-login\nimport Base\n\n# source: spec-auth-user-login "
        f"§3.1 sha256:{source_hash}\nlaw a:\n  for x: Nat\n  {{x == x : Nat}}\n",
        encoding="utf-8")
    return spec


class TestSpecLawsReminder:
    REL = os.path.join(".sdd", "specification", "auth", "user-login_spec.md")

    def test_drifted_law_is_named(self, tmp_path, capsys):
        _spec_with_laws(tmp_path, "0" * 12)
        _process(self.REL, tmp_path)
        out = capsys.readouterr().out
        assert "/draft-laws" in out and "a (§3.1, source_drift)" in out

    def test_in_sync_still_suggests_without_naming(self, tmp_path, capsys):
        import laws_drafting as ld
        spec = _spec_with_laws(tmp_path, "0" * 12)
        h = ld.section_hash(spec.read_text(encoding="utf-8"), "3.1")
        laws = tmp_path / ".sdd" / "laws" / "auth" / "user-login" / "LAWS.bend"
        laws.write_text(laws.read_text(encoding="utf-8").replace("0" * 12, h), encoding="utf-8")
        _process(self.REL, tmp_path)
        out = capsys.readouterr().out
        assert "/draft-laws" in out and "source_drift" not in out

    def test_spec_without_laws_has_no_laws_reminder(self, tmp_path, capsys):
        spec = tmp_path / ".sdd" / "specification" / "a_spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text('---\nid: "x"\n---\n# a\n', encoding="utf-8")
        _process(os.path.join(".sdd", "specification", "a_spec.md"), tmp_path)
        assert "/draft-laws" not in capsys.readouterr().out

    def test_spec_sync_and_laws_reminder_are_one_json(self, tmp_path, capsys):
        import json
        _spec_with_laws(tmp_path, "0" * 12)
        _process(self.REL, tmp_path)
        lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
        assert len(lines) == 1
        ctx = json.loads(lines[0])["hookSpecificOutput"]["additionalContext"]
        assert "PRD <-> spec <-> adr" in ctx and "/draft-laws" in ctx

    def test_model_of_and_sync_are_one_json(self, tmp_path, capsys):
        import json
        _laws_project(tmp_path)
        (tmp_path / ".sdd" / "specification").mkdir(parents=True)
        (tmp_path / ".sdd" / "specification" / "user_login_spec.md").write_text("x", encoding="utf-8")
        (tmp_path / "src" / "auth").mkdir(parents=True)
        _process(os.path.join("src", "auth", "user_login.py"), tmp_path)
        lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
        assert len(lines) == 1 and "# model-of:" in json.loads(lines[0])["hookSpecificOutput"]["additionalContext"]
