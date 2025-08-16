import sqlite3
import logging
import numpy as np
import pathlib
import sys
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "sparc-server"))

import enhanced_embeddings as ee


def test_semantic_search_handles_zero_vectors(monkeypatch, caplog):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE decisions (
            id INTEGER PRIMARY KEY,
            summary TEXT,
            rationale TEXT,
            phase_name TEXT,
            timestamp TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO decisions (summary, rationale, phase_name, timestamp) VALUES (?, ?, ?, ?)",
        ("s", "r", "p", "t"),
    )
    decision_id = conn.execute("SELECT id FROM decisions").fetchone()[0]
    provider = ee.TFIDFEmbeddingProvider()
    searcher = ee.EnhancedSPARCSearch(conn, provider)
    zero_vec = np.zeros(2)
    conn.execute(
        "INSERT INTO item_embeddings (item_type, item_id, embedding, text_content, embedding_model, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("decisions", decision_id, zero_vec.tobytes(), "text", provider.name, "now"),
    )
    conn.commit()
    monkeypatch.setattr(provider, "encode", lambda texts: np.array([zero_vec]))
    with caplog.at_level(logging.WARNING):
        results = searcher.semantic_search("q", top_k=1, min_similarity=0.0)
        assert results[0].similarity_score == 0.0
        assert "Zero-magnitude embedding detected" in caplog.text

