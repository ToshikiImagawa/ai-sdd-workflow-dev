"""fm_parser.py のユニットテスト（pytest）。

front matter 境界検出、split、parse、および CRLF・空白を吸収する
delimiter 判定（strip 統一）を検証する。
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "fm_parser.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("fm_parser", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fp = _load_module()


class TestFindFrontMatterBounds:
    def test_with_front_matter(self):
        lines = ["---", "id: x", "title: T", "---", "# Body"]
        assert fp.find_front_matter_bounds(lines) == (True, 3)

    def test_without_front_matter(self):
        assert fp.find_front_matter_bounds(["# Heading", "body"]) == (False, 0)

    def test_unclosed(self):
        assert fp.find_front_matter_bounds(["---", "id: x", "no close"]) == (False, 0)

    def test_closing_beyond_50_lines(self):
        lines = ["---"] + [f"k{i}: v" for i in range(60)] + ["---"]
        assert fp.find_front_matter_bounds(lines) == (False, 0)

    def test_empty(self):
        assert fp.find_front_matter_bounds([]) == (False, 0)

    def test_has_front_matter_is_alias(self):
        assert fp.has_front_matter is fp.find_front_matter_bounds

    def test_crlf_delimiter_tolerated(self):
        # splitlines() drops \r\n, but a stray trailing CR on the fence still detects.
        assert fp.find_front_matter_bounds(["---\r", "id: x", "---\r"]) == (True, 2)

    def test_whitespace_padded_delimiter_tolerated(self):
        # strip() unifies the two former implementations (rstrip('\\r') vs strip()).
        assert fp.find_front_matter_bounds(["  ---  ", "id: x", " --- "]) == (True, 2)


class TestSplitFrontMatter:
    def test_with_front_matter(self):
        fm, body = fp.split_front_matter("---\nid: a\ntitle: T\n---\n# Body")
        assert fm == "id: a\ntitle: T"
        assert body == "# Body"

    def test_without_front_matter(self):
        text = "# Just body\nno fm"
        assert fp.split_front_matter(text) == ("", text)

    def test_unclosed_returns_whole_text(self):
        text = "---\nid: a\nno closing fence"
        assert fp.split_front_matter(text) == ("", text)


class TestParseFrontMatter:
    def test_scalars(self):
        assert fp.parse_front_matter("id: prd-auth\ntitle: Auth") == {
            "id": "prd-auth", "title": "Auth",
        }

    def test_quoted_scalar_stripped(self):
        assert fp.parse_front_matter('title: "Hello"') == {"title": "Hello"}

    def test_inline_list(self):
        assert fp.parse_front_matter("tags: [a, b, c]") == {"tags": ["a", "b", "c"]}

    def test_block_list(self):
        result = fp.parse_front_matter("depends-on:\n  - x\n  - y")
        assert result == {"depends-on": ["x", "y"]}

    def test_empty(self):
        assert fp.parse_front_matter("") == {}

    def test_non_list_key_single_value(self):
        assert fp.parse_front_matter("status: draft") == {"status": "draft"}
