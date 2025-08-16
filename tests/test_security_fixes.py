import sqlite3
import pathlib
import sqlite3
import sys
import tempfile
import os

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "sparc-server"))

from enhanced_embeddings import EnhancedSPARCSearch, TFIDFEmbeddingProvider
from specialized_mcp_server import ContextPortalSPARCServer


def setup_embeddings_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE decisions (id INTEGER PRIMARY KEY, summary TEXT, rationale TEXT)"
    )
    conn.execute(
        "INSERT INTO decisions (id, summary, rationale) VALUES (1, 'sum1', 'rat1')"
    )
    provider = TFIDFEmbeddingProvider()
    search = EnhancedSPARCSearch(conn, provider)
    return conn, search


def test_update_embeddings_and_search():
    conn, search = setup_embeddings_db()
    search.update_embeddings("decisions", [1])
    rows = conn.execute("SELECT item_type, item_id FROM item_embeddings").fetchall()
    assert rows and rows[0]["item_id"] == 1

    results = search.semantic_search("sum1", filter_item_types=["decisions"])
    assert results and results[0].item_id == 1

    results_none = search.semantic_search("sum1", filter_item_types=["progress"])
    assert results_none == []


def setup_server() -> ContextPortalSPARCServer:
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    return ContextPortalSPARCServer(workspace_dir=tmpdir, db_path=db_path)


def test_update_progress_and_search_custom_data():
    server = setup_server()
    c = server._conn.cursor()
    c.execute(
        "INSERT INTO progress (status, description, parent_id, timestamp) VALUES (?, ?, ?, ?)",
        ("open", "desc", None, "t"),
    )
    progress_id = c.lastrowid
    server.update_progress(progress_id, status="closed", description="done")
    row = c.execute(
        "SELECT status, description FROM progress WHERE id = ?", (progress_id,)
    ).fetchone()
    assert row["status"] == "closed"
    assert row["description"] == "done"

    server.log_custom_data("cat", "k1", {"foo": "bar"})
    results = server.search_custom_data_value_fts("bar", category_filter="cat", limit=5)
    assert results and results[0]["category"] == "cat"

