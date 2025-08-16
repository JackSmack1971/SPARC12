import os
import sys
import pathlib
import numpy as np
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "sparc-server"))

import enhanced_embeddings as ee


class DummyEmbeddings:
    async def create(self, model: str, input: list):
        return type(
            "Resp",
            (),
            {"data": [type("Item", (), {"embedding": [1.0, 2.0]}) for _ in input]},
        )


class DummyClient:
    def __init__(self, *args, **kwargs):
        self.embeddings = DummyEmbeddings()


def test_missing_api_token_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_TOKEN", raising=False)
    monkeypatch.setattr(ee, "HAS_OPENAI", True)
    with pytest.raises(ValueError):
        ee.OpenAIEmbeddingProvider()


def test_init_uses_env_token_and_no_global(monkeypatch):
    monkeypatch.setenv("OPENAI_API_TOKEN", "k")
    monkeypatch.setattr(ee, "AsyncOpenAI", DummyClient)
    import openai

    openai.api_key = None
    provider = ee.OpenAIEmbeddingProvider()
    assert getattr(openai, "api_key", None) is None
    assert provider._api_key == "k"


def test_encode_returns_embeddings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_TOKEN", "k")
    monkeypatch.setattr(ee, "AsyncOpenAI", DummyClient)
    provider = ee.OpenAIEmbeddingProvider()
    result = provider.encode(["a"])
    assert isinstance(result, np.ndarray)
    assert result.shape == (1, 2)
