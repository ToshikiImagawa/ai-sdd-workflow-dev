"""user-prompt-submit.py のユニットテスト（pytest）。

Vibe Coding 曖昧表現の日本語/英語 4 カテゴリ検出と、
明確な指示での空返却を検証する。リファクタ前の安全網。
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "sdd-workflow" / "scripts" / "user-prompt-submit.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("user_prompt_submit", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ups = _load_module()


class TestDetectVagueExpressions:
    @pytest.mark.parametrize("prompt,label", [
        ("いい感じにして", "subjective expression"),
        ("make it nice", "subjective expression"),
        ("とりあえず動くように", "unclear degree"),
        ("a bit faster please", "unclear degree"),
        ("前と同じでよろしく", "ambiguous scope / implicit assumption"),
        ("same as before", "ambiguous scope / implicit assumption"),
        ("できればついでに", "ambiguous priority"),
        ("if possible", "ambiguous priority"),
    ])
    def test_detects_category(self, prompt, label):
        matched = ups.detect_vague_expressions(prompt)
        assert any(item.startswith(label) for item in matched)

    def test_clear_instruction_returns_empty(self):
        prompt = "Add a POST /users endpoint that returns 201 with the created user id."
        assert ups.detect_vague_expressions(prompt) == []

    def test_case_insensitive(self):
        assert ups.detect_vague_expressions("MAKE IT NICE")

    def test_multiple_signals_all_reported(self):
        matched = ups.detect_vague_expressions("いい感じに、できれば速く")
        assert len(matched) >= 2
