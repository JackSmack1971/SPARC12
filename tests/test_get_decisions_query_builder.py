import tempfile
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "sparc-server"))
from specialized_mcp_server import (
    ContextPortalSPARCServer,
    QueryBuilderError,
    DatabaseQueryError,
)


def _server() -> ContextPortalSPARCServer:
    tmpdir = tempfile.mkdtemp()
    return ContextPortalSPARCServer(workspace_dir=tmpdir)


def test_build_decisions_query_basic() -> None:
    server = _server()
    query, params = server.build_decisions_query()
    assert query == "SELECT * FROM decisions ORDER BY id DESC"
    assert params == []


def test_build_decisions_query_filters_limit() -> None:
    server = _server()
    query, params = server.build_decisions_query(
        tags_filter_include_all=["a"], tags_filter_include_any=["b"], limit=5
    )
    expected = (
        "SELECT * FROM decisions WHERE tags LIKE ? AND (tags LIKE ?) ORDER BY id DESC LIMIT 5"
    )
    assert query == expected
    assert params == ["%a%", "%b%"]


def test_build_decisions_query_invalid_tags() -> None:
    server = _server()
    with pytest.raises(QueryBuilderError):
        server.build_decisions_query(tags_filter_include_all="bad")


def test_get_decisions_filters_results() -> None:
    server = _server()
    server.log_decision("s1", "r1", tags=["alpha", "beta"])
    server.log_decision("s2", "r2", tags=["beta", "gamma"])
    rows = server.get_decisions(
        tags_filter_include_all=["beta"], tags_filter_include_any=["gamma"]
    )
    assert len(rows) == 1 and rows[0]["summary"] == "s2"


def test_get_decisions_db_error() -> None:
    server = _server()
    c = server._conn.cursor()
    c.execute("DROP TABLE decisions")
    server._conn.commit()
    with pytest.raises(DatabaseQueryError):
        server.get_decisions()
