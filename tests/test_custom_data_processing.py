import sqlite3
import sys
import pathlib
import logging
import json
import numpy as np
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "sparc-server"))

from enhanced_embeddings import (
    EnhancedSPARCSearch,
    EmbeddingProvider,
    CustomDataProcessingError,
)


class DummyProvider(EmbeddingProvider):
    def encode(self, texts):
        return np.zeros((len(texts), 1))

    def get_dimension(self):
        return 1

    @property
    def name(self):
        return "dummy"


def setup_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "CREATE TABLE custom_data (id INTEGER PRIMARY KEY, category TEXT, key TEXT, value TEXT)"
    )
    return conn


def test_get_item_text_content_parses_json_object():
    conn = setup_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO custom_data (id, category, key, value) VALUES (?, ?, ?, ?)",
        (1, "cat", "k", '{"a":1}')
    )
    search = EnhancedSPARCSearch(conn, DummyProvider())
    result = search._get_item_text_content("custom_data", 1)
    assert result == "cat/k: {\"a\":1}"


def test_get_item_text_content_invalid_json_logs_warning(caplog):
    conn = setup_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO custom_data (id, category, key, value) VALUES (?, ?, ?, ?)",
        (1, "cat", "k", "invalid")
    )
    search = EnhancedSPARCSearch(conn, DummyProvider())
    with caplog.at_level(logging.WARNING):
        result = search._get_item_text_content("custom_data", 1)
    assert result == "cat/k: invalid"
    assert "Failed to parse JSON value for custom_data id 1" in caplog.text


def test_get_item_text_content_unexpected_error(monkeypatch):
    conn = setup_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO custom_data (id, category, key, value) VALUES (?, ?, ?, ?)",
        (1, "cat", "k", "42")
    )
    search = EnhancedSPARCSearch(conn, DummyProvider())

    def boom(_):
        raise RuntimeError("boom")

    monkeypatch.setattr(json, "loads", lambda *args, **kwargs: boom(None))
    with pytest.raises(CustomDataProcessingError):
        search._get_item_text_content("custom_data", 1)
