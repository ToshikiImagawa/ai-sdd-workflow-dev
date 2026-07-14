#!/usr/bin/env python3
"""tokenizer.py - count_tokens abstraction for the Issue #16 A/B harness.

The A/B measurement registers "real tokenizer, no approximation" as a
pre-committed rule. This module resolves a token-counting backend in priority
order and, when none is available, returns None so the aggregator emits a
"判定保留 (inconclusive)" verdict instead of silently falling back to an
approximation.

Backends (in order):
  1. anthropic direct API — anthropic.Anthropic().messages.count_tokens.
     Requires ANTHROPIC_API_KEY. Model via SDD_TOKENIZER_MODEL
     (default claude-sonnet-4-5-20250929).
  2. Vertex AI — anthropic.AnthropicVertex().messages.count_tokens.
     Requires `pip install 'anthropic[vertex]'` and GCP ADC (gcloud auth
     application-default login). Project/region from ANTHROPIC_VERTEX_PROJECT_ID
     / GOOGLE_CLOUD_PROJECT and CLOUD_ML_REGION / GOOGLE_CLOUD_LOCATION.
     Model via SDD_TOKENIZER_MODEL (default claude-sonnet-4-5@20250929).
  3. None — caller treats token counts as unavailable (verdict=inconclusive).

char/byte length are exposed as SANITY-CHECK reference values only; they are
never used as the primary indicator.
"""

import os
from typing import Optional


class Tokenizer:
    def __init__(self) -> None:
        self.backend_name = "none"
        self._client = None
        self._model = ""
        self._init_backend()

    def _init_backend(self) -> None:
        # 1. anthropic direct API (API key)
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                import anthropic  # type: ignore
                self._client = anthropic.Anthropic()
                self._model = os.environ.get("SDD_TOKENIZER_MODEL", "claude-sonnet-4-5-20250929")
                self.backend_name = "anthropic.count_tokens"
                return
            except Exception:  # noqa: BLE001 - fall through
                self._client = None

        # 2. Vertex AI (google cloud ADC). No API key needed.
        vertex_project = (os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
                          or os.environ.get("GOOGLE_CLOUD_PROJECT"))
        if vertex_project:
            try:
                from anthropic import AnthropicVertex  # type: ignore
                region = (os.environ.get("CLOUD_ML_REGION")
                          or os.environ.get("GOOGLE_CLOUD_LOCATION")
                          or "us-east5")
                self._client = AnthropicVertex(project_id=vertex_project, region=region)
                self._model = os.environ.get("SDD_TOKENIZER_MODEL", "claude-sonnet-4-5@20250929")
                self.backend_name = "anthropic.vertex.count_tokens"
                return
            except Exception:  # noqa: BLE001 - fall through
                self._client = None

        # 3. no backend
        self.backend_name = "none"

    @property
    def available(self) -> bool:
        return self.backend_name != "none"

    def count(self, text: str) -> Optional[int]:
        """Return token count, or None when no real backend is available."""
        if not text:
            return 0
        if self._client is not None and self.backend_name != "none":
            try:
                resp = self._client.messages.count_tokens(
                    model=self._model,
                    messages=[{"role": "user", "content": text}],
                )
                return int(resp.input_tokens)
            except Exception:  # noqa: BLE001 - treat as unavailable
                return None
        return None

    @staticmethod
    def char_len(text: str) -> int:
        return len(text)

    @staticmethod
    def byte_len(text: str) -> int:
        return len(text.encode("utf-8"))
