"""sdd_index.py のユニットテスト（pytest）。

スキーマ初期化、フロントマターパース、要求ID抽出、SysMLパース、
キャッシュ無効化、テーブル形式 index.md 生成を検証する。
"""

import importlib.util
import os
import sqlite3
import textwrap
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "sdd_index.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("sdd_index", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


si = _load_module()


# --- front matter ---------------------------------------------------------

class TestSplitFrontMatter:
    def test_with_front_matter(self):
        text = "---\nid: prd-auth\ntitle: Auth\n---\n# Body"
        fm, body = si.split_front_matter(text)
        assert fm == "id: prd-auth\ntitle: Auth"
        assert body == "# Body"

    def test_without_front_matter(self):
        text = "# Just a heading\nSome text"
        fm, body = si.split_front_matter(text)
        assert fm == ""
        assert body == text

    def test_unclosed_front_matter(self):
        text = "---\nid: test\nno closing"
        fm, body = si.split_front_matter(text)
        assert fm == ""
        assert body == text


class TestParseFrontMatter:
    def test_all_fields(self):
        fm = textwrap.dedent("""\
            id: prd-auth
            title: Authentication
            type: prd
            status: approved
            category: auth
            sdd-phase: specify
            impl-status: in-progress
            priority: high
            risk: medium
            created: 2026-01-01
            updated: 2026-07-14
        """)
        result = si.parse_front_matter(fm)
        assert result["id"] == "prd-auth"
        assert result["title"] == "Authentication"
        assert result["type"] == "prd"
        assert result["priority"] == "high"
        assert result["risk"] == "medium"
        assert result["created"] == "2026-01-01"
        assert result["updated"] == "2026-07-14"

    def test_depends_on_inline(self):
        fm = 'depends-on: [prd-auth, prd-core]'
        result = si.parse_front_matter(fm)
        assert result["depends-on"] == ["prd-auth", "prd-core"]

    def test_depends_on_block(self):
        fm = "depends-on:\n  - prd-auth\n  - prd-core"
        result = si.parse_front_matter(fm)
        assert result["depends-on"] == ["prd-auth", "prd-core"]

    def test_tags(self):
        fm = "tags: [auth, security]"
        result = si.parse_front_matter(fm)
        assert result["tags"] == ["auth", "security"]

    def test_quoted_values(self):
        fm = 'id: "spec-auth"\ntitle: \'Auth Spec\''
        result = si.parse_front_matter(fm)
        assert result["id"] == "spec-auth"
        assert result["title"] == "Auth Spec"

    def test_empty_string(self):
        result = si.parse_front_matter("")
        assert result == {}


# --- body extraction ------------------------------------------------------

class TestExtractReqIds:
    def test_heading_def(self):
        body = "# UR-001 User Login"
        result = si.extract_sections_and_scan(body)
        ids = result["req_ids"]
        assert len(ids) == 1
        assert ids[0]["req_id"] == "UR-001"
        assert ids[0]["kind"] == "def"

    def test_table_row_def(self):
        body = "| **FR-001** | Login | Must |"
        result = si.extract_sections_and_scan(body)
        ids = result["req_ids"]
        assert any(r["req_id"] == "FR-001" and r["kind"] == "def" for r in ids)

    def test_inline_ref(self):
        body = "# Section\nThis references FR-001 for login."
        result = si.extract_sections_and_scan(body)
        ids = result["req_ids"]
        assert any(r["req_id"] == "FR-001" and r["kind"] == "ref" for r in ids)

    def test_def_overrides_ref(self):
        body = "See FR-001.\n# FR-001 Login Feature"
        result = si.extract_sections_and_scan(body)
        ids = result["req_ids"]
        fr001 = [r for r in ids if r["req_id"] == "FR-001"]
        assert len(fr001) == 1
        assert fr001[0]["kind"] == "def"


class TestExtractSysml:
    def test_sysml_relationships(self):
        body = textwrap.dedent("""\
            # Requirements
            ```mermaid
            requirementDiagram
                requirement "User Login" {
                    id: UR-001
                }
                UR-001 - deriveReqt -> FR-001
                FR-001 - satisfy -> DC-001
            ```
        """)
        result = si.extract_sections_and_scan(body)
        rels = result["sysml_relationships"]
        assert len(rels) == 2
        assert rels[0]["source_id"] == "UR-001"
        assert rels[0]["rel_type"] == "deriveReqt"
        assert rels[0]["target_id"] == "FR-001"
        assert rels[1]["source_id"] == "FR-001"
        assert rels[1]["rel_type"] == "satisfy"
        assert rels[1]["target_id"] == "DC-001"

    def test_non_sysml_mermaid_ignored(self):
        body = "```mermaid\ngraph TD\n  A --> B\n```"
        result = si.extract_sections_and_scan(body)
        assert result["sysml_relationships"] == []


class TestExtractDataModels:
    def test_json_block(self):
        body = '# Data\n```json\n{"user_id": "string"}\n```'
        result = si.extract_sections_and_scan(body)
        assert len(result["data_models"]) == 1
        assert result["data_models"][0]["lang"] == "json"

    def test_non_data_lang_ignored(self):
        body = "```bash\necho hello\n```"
        result = si.extract_sections_and_scan(body)
        assert result["data_models"] == []


class TestExtractApi:
    def test_http_method(self):
        body = "POST /api/auth/login"
        result = si.extract_sections_and_scan(body)
        sigs = result["api_signatures"]
        assert any("POST /api/auth/login" in s["signature"] for s in sigs)


class TestExtractSysmlElements:
    def test_requirement_and_element_nodes(self):
        body = textwrap.dedent("""\
            # Requirements
            ```mermaid
            requirementDiagram
                requirement "User Login" {
                    id: UR-001
                    text: The user can log in.
                    risk: high
                    verifymethod: test
                }
                functionalRequirement fr_login {
                    id: FR-001
                }
                element login_service {
                    type: simulation
                    docref: design.md
                }
                UR-001 - deriveReqt -> FR-001
            ```
        """)
        result = si.extract_sections_and_scan(body)
        elems = result["sysml_elements"]
        by_name = {e["name"]: e for e in elems}
        assert "User Login" in by_name
        assert by_name["User Login"]["kind"] == "requirement"
        assert by_name["User Login"]["keyword"] == "requirement"
        assert by_name["User Login"]["req_id"] == "UR-001"
        assert by_name["fr_login"]["keyword"] == "functionalRequirement"
        assert by_name["fr_login"]["req_id"] == "FR-001"
        assert by_name["login_service"]["kind"] == "element"
        assert by_name["login_service"]["elem_type"] == "simulation"
        # relationship extraction stays intact alongside node extraction
        assert any(r["source_id"] == "UR-001" for r in result["sysml_relationships"])

    def test_semicolon_separated_body(self):
        body = textwrap.dedent("""\
            ```mermaid
            requirementDiagram
                requirement req_a { id: UR-002; risk: low }
            ```
        """)
        result = si.extract_sections_and_scan(body)
        elems = result["sysml_elements"]
        assert len(elems) == 1
        assert elems[0]["name"] == "req_a"
        assert elems[0]["req_id"] == "UR-002"

    def test_non_sysml_mermaid_ignored(self):
        body = "```mermaid\ngraph TD\n  A --> B\n```"
        result = si.extract_sections_and_scan(body)
        assert result["sysml_elements"] == []


class TestExtractDataModelFields:
    def test_json_keys(self):
        body = '```json\n{"user_id": "string", "email": "string"}\n```'
        result = si.extract_sections_and_scan(body)
        fields = [f["field_name"] for f in result["data_model_fields"]]
        assert "user_id" in fields
        assert "email" in fields

    def test_typescript_properties(self):
        body = textwrap.dedent("""\
            ```typescript
            interface User {
                id: string;
                name?: string;
                readonly createdAt: Date;
            }
            ```
        """)
        result = si.extract_sections_and_scan(body)
        fields = [f["field_name"] for f in result["data_model_fields"]]
        assert "id" in fields
        assert "name" in fields
        assert "createdAt" in fields

    def test_yaml_top_level_keys(self):
        body = textwrap.dedent("""\
            ```yaml
            user_id: string
            profile:
              name: string
            ```
        """)
        result = si.extract_sections_and_scan(body)
        fields = [f["field_name"] for f in result["data_model_fields"]]
        assert "user_id" in fields
        assert "profile" in fields
        # nested key is indented -> not a top-level key
        assert "name" not in fields

    def test_sql_columns(self):
        body = textwrap.dedent("""\
            ```sql
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL,
                PRIMARY KEY (id)
            );
            ```
        """)
        result = si.extract_sections_and_scan(body)
        fields = [f["field_name"] for f in result["data_model_fields"]]
        assert "id" in fields
        assert "email" in fields
        # constraint keyword must not be captured as a column
        assert "PRIMARY" not in fields

    def test_python_attributes(self):
        body = textwrap.dedent("""\
            ```python
            class User:
                id: int
                email: str = ""
            ```
        """)
        result = si.extract_sections_and_scan(body)
        fields = [f["field_name"] for f in result["data_model_fields"]]
        assert "id" in fields
        assert "email" in fields


# --- schema & hashing ----------------------------------------------------

class TestSchema:
    def test_init_creates_tables(self):
        conn = sqlite3.connect(":memory:")
        si.init_schema(conn)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        assert "documents" in tables
        assert "sysml_relationships" in tables
        assert "sysml_elements" in tables
        assert "data_model_fields" in tables
        assert "tags" in tables
        assert "meta" in tables
        version = conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()
        assert version[0] == si.SCHEMA_VERSION

    def test_migration_on_version_mismatch(self):
        """旧スキーマ版数のDBは、現行 SCHEMA_VERSION と異なれば
        全テーブルを再構築（マイグレーション）する。"""
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO meta VALUES('schema_version', ?)",
            (si.SCHEMA_VERSION + "-old",),
        )
        conn.execute("CREATE TABLE documents (path TEXT PRIMARY KEY, doc_id TEXT)")
        conn.commit()
        si.init_schema(conn)
        version = conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()
        assert version[0] == si.SCHEMA_VERSION
        cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
        assert "content_hash" in cols
        assert "priority" in cols

    def test_idempotent(self):
        conn = sqlite3.connect(":memory:")
        si.init_schema(conn)
        si.init_schema(conn)
        version = conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()
        assert version[0] == si.SCHEMA_VERSION


class TestFileHash:
    def test_consistent(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello world", encoding="utf-8")
        h1 = si.file_hash(str(f))
        h2 = si.file_hash(str(f))
        assert h1 == h2
        assert len(h1) == 64

    def test_different_content(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("aaa", encoding="utf-8")
        f2.write_text("bbb", encoding="utf-8")
        assert si.file_hash(str(f1)) != si.file_hash(str(f2))


# --- rebuild + cache invalidation ----------------------------------------

def _create_sdd_project(tmp_path):
    """Create a minimal .sdd project structure for testing."""
    sdd = tmp_path / ".sdd"
    req = sdd / "requirement"
    spec = sdd / "specification"
    req.mkdir(parents=True)
    spec.mkdir(parents=True)
    config = tmp_path / ".sdd-config.json"
    config.write_text('{"root":".sdd","lang":"en","directories":{"requirement":"requirement","specification":"specification"}}')
    return tmp_path


def _write_prd(tmp_path, name, content):
    f = tmp_path / ".sdd" / "requirement" / f"{name}.md"
    f.write_text(content, encoding="utf-8")
    return f


class TestRebuildAll:
    def test_basic_rebuild(self, tmp_path):
        proj = _create_sdd_project(tmp_path)
        _write_prd(proj, "auth", textwrap.dedent("""\
            ---
            id: prd-auth
            title: Authentication
            type: prd
            status: approved
            priority: high
            risk: medium
            created: 2026-01-01
            updated: 2026-07-14
            depends-on: []
            tags: [auth]
            ---
            # UR-001 User Login
        """))
        si.rebuild_all(str(proj))

        db = str(proj / ".sdd" / ".cache" / "index.sqlite")
        assert os.path.isfile(db)
        conn = sqlite3.connect(db)
        docs = conn.execute("SELECT doc_id, type, priority FROM documents").fetchall()
        assert len(docs) == 1
        assert docs[0] == ("prd-auth", "prd", "high")

        ids = conn.execute("SELECT req_id, kind FROM ids").fetchall()
        assert ("UR-001", "def") in ids

        tags = conn.execute("SELECT tag FROM tags").fetchall()
        assert ("auth",) in tags

        md_file = str(proj / ".sdd" / ".cache" / "index.md")
        assert os.path.isfile(md_file)
        content = open(md_file).read()
        assert "## Metadata" in content
        assert "prd-auth" in content
        conn.close()

    def test_skip_unchanged(self, tmp_path):
        proj = _create_sdd_project(tmp_path)
        _write_prd(proj, "auth", "---\nid: prd-auth\ntype: prd\n---\n# UR-001")
        si.rebuild_all(str(proj))
        md1 = (proj / ".sdd" / ".cache" / "index.md").stat().st_mtime_ns

        import time
        time.sleep(0.05)
        si.rebuild_all(str(proj))
        md2 = (proj / ".sdd" / ".cache" / "index.md").stat().st_mtime_ns
        # index.md should NOT be regenerated since content unchanged
        assert md1 == md2

    def test_stale_file_removal(self, tmp_path):
        proj = _create_sdd_project(tmp_path)
        f = _write_prd(proj, "old", "---\nid: prd-old\ntype: prd\n---\n# body")
        si.rebuild_all(str(proj))
        conn = sqlite3.connect(str(proj / ".sdd" / ".cache" / "index.sqlite"))
        assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 1
        conn.close()

        f.unlink()
        si.rebuild_all(str(proj))
        conn = sqlite3.connect(str(proj / ".sdd" / ".cache" / "index.sqlite"))
        assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
        conn.close()


class TestUpdateOne:
    def test_incremental_update(self, tmp_path):
        proj = _create_sdd_project(tmp_path)
        _write_prd(proj, "auth", "---\nid: prd-auth\ntype: prd\n---\n# UR-001")
        si.rebuild_all(str(proj))

        _write_prd(proj, "auth", "---\nid: prd-auth\ntype: prd\n---\n# UR-001\n# UR-002")
        si.update_one(str(proj), ".sdd/requirement/auth.md")

        conn = sqlite3.connect(str(proj / ".sdd" / ".cache" / "index.sqlite"))
        ids = conn.execute("SELECT req_id FROM ids ORDER BY req_id").fetchall()
        assert ("UR-001",) in ids
        assert ("UR-002",) in ids
        conn.close()

    def test_noop_without_db(self, tmp_path):
        proj = _create_sdd_project(tmp_path)
        si.update_one(str(proj), ".sdd/requirement/auth.md")
        assert not os.path.isfile(str(proj / ".sdd" / ".cache" / "index.sqlite"))

    def test_hash_skip(self, tmp_path):
        proj = _create_sdd_project(tmp_path)
        _write_prd(proj, "auth", "---\nid: prd-auth\ntype: prd\n---\n# UR-001")
        si.rebuild_all(str(proj))
        md1 = (proj / ".sdd" / ".cache" / "index.md").stat().st_mtime_ns

        import time
        time.sleep(0.05)
        si.update_one(str(proj), ".sdd/requirement/auth.md")
        md2 = (proj / ".sdd" / ".cache" / "index.md").stat().st_mtime_ns
        assert md1 == md2


# --- derive_index table format --------------------------------------------

class TestDeriveIndexFormat:
    def test_table_format_sections(self, tmp_path):
        proj = _create_sdd_project(tmp_path)
        _write_prd(proj, "auth", textwrap.dedent("""\
            ---
            id: prd-auth
            title: Auth
            type: prd
            status: approved
            depends-on: []
            ---
            # UR-001 User Login
            ```mermaid
            requirementDiagram
                requirement "User Login" {
                    id: UR-001
                }
                element login_service {
                    type: simulation
                }
                UR-001 - deriveReqt -> FR-001
            ```
            ```json
            {"user_id": "string"}
            ```
            POST /api/auth/login
        """))
        si.rebuild_all(str(proj))

        content = (proj / ".sdd" / ".cache" / "index.md").read_text()
        assert "## Metadata" in content
        assert "## Requirement IDs" in content
        assert "## SysML Relationships" in content
        assert "## SysML Elements" in content
        assert "## API Signatures" in content
        assert "## Data Models" in content
        assert "## Data Model Fields" in content
        assert "| prd-auth |" in content
        assert "| UR-001 | def |" in content
        assert "| UR-001 | deriveReqt | FR-001 |" in content
        assert "| POST /api/auth/login |" in content
        assert "| login_service | element |" in content
        assert "| user_id |" in content


# --- post-tool-use MultiEdit support -------------------------------------

class TestPostToolUseExtractPaths:
    def _load_post_tool_use(self):
        path = (
            Path(__file__).resolve().parent.parent
            / "plugins" / "sdd-workflow" / "scripts" / "post-tool-use.py"
        )
        spec = importlib.util.spec_from_file_location("post_tool_use", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_write_single_file(self):
        ptu = self._load_post_tool_use()
        payload = {"tool_input": {"file_path": "/proj/src/main.py"}}
        assert ptu._extract_file_paths(payload) == ["/proj/src/main.py"]

    def test_multiedit_multiple_files(self):
        ptu = self._load_post_tool_use()
        payload = {"tool_input": {"edits": [
            {"file_path": "/proj/a.md"},
            {"file_path": "/proj/b.md"},
            {"file_path": "/proj/a.md"},
        ]}}
        result = ptu._extract_file_paths(payload)
        assert result == ["/proj/a.md", "/proj/b.md"]

    def test_empty_input(self):
        ptu = self._load_post_tool_use()
        payload = {"tool_input": {}}
        assert ptu._extract_file_paths(payload) == []
