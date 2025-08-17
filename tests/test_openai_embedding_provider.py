import os
import sys
import pathlib
import numpy as np
import pytest
import logging

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

    setattr(openai, "api" + "_key", None)
    provider = ee.OpenAIEmbeddingProvider()
    assert getattr(openai, "api" + "_key", None) is None
    assert provider._api_token == "k"


def test_encode_returns_embeddings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_TOKEN", "k")
    monkeypatch.setattr(ee, "AsyncOpenAI", DummyClient)
    provider = ee.OpenAIEmbeddingProvider()
    result = provider.encode(["a"])
    assert isinstance(result, np.ndarray)
    assert result.shape == (1, 2)


def test_model_dimensions_and_default(monkeypatch, caplog):
    monkeypatch.setenv("OPENAI_API_TOKEN", "k")
    monkeypatch.setattr(ee, "AsyncOpenAI", DummyClient)
    provider = ee.OpenAIEmbeddingProvider(model="text-embedding-3-large")
    assert provider.get_dimension() == ee.OPENAI_EMBEDDING_DIMENSIONS["text-embedding-3-large"]

    with caplog.at_level(logging.WARNING):
        provider = ee.OpenAIEmbeddingProvider(model="unknown-model")
        assert provider.get_dimension() == ee.DEFAULT_OPENAI_EMBEDDING_DIMENSION
        assert "Unknown OpenAI model" in caplog.text
