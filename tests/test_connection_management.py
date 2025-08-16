import os
import sqlite3
import tempfile
import sys
import pathlib

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "sparc-server"))

from specialized_mcp_server import ContextPortalSPARCServer, DatabaseConnectionError


def test_context_manager_closes_connection() -> None:
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "ctx.db")
    with ContextPortalSPARCServer(workspace_dir=tmpdir, db_path=db_path) as server:
        assert server._conn is not None
        server._conn.execute("SELECT 1")
    assert server._conn is None


def test_close_method_closes_connection() -> None:
    tmpdir = tempfile.mkdtemp()
    server = ContextPortalSPARCServer(workspace_dir=tmpdir)
    assert server._conn is not None
    server.close()
    assert server._conn is None


def test_connect_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def bad_connect(*args, **kwargs):
        raise sqlite3.OperationalError("fail")

    monkeypatch.setattr(sqlite3, "connect", bad_connect)
    tmpdir = tempfile.mkdtemp()
    with pytest.raises(DatabaseConnectionError):
        ContextPortalSPARCServer(workspace_dir=tmpdir)
