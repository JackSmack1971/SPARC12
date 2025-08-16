import tempfile
from pathlib import Path
import sys
import sqlite3

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "sparc-server"))
from specialized_mcp_server import ContextPortalSPARCServer, DatabaseQueryError


def test_get_current_phase_returns_active_phase() -> None:
    tmpdir = tempfile.mkdtemp()
    server = ContextPortalSPARCServer(workspace_dir=tmpdir)
    c = server._conn.cursor()
    try:
        c.execute("UPDATE phases SET status='pending'")
        c.execute("UPDATE phases SET status='active' WHERE name=?", ("design",))
        server._conn.commit()
    finally:
        c.close()
    assert server.get_current_phase() == "design"
    server.close()


def test_get_current_phase_fallback_to_first() -> None:
    tmpdir = tempfile.mkdtemp()
    server = ContextPortalSPARCServer(workspace_dir=tmpdir)
    c = server._conn.cursor()
    try:
        c.execute("UPDATE phases SET status='pending'")
        server._conn.commit()
    finally:
        c.close()
    assert server.get_current_phase() == server.PHASE_SEQUENCE[0]
    server.close()


def test_get_current_phase_database_error(monkeypatch: pytest.MonkeyPatch) -> None:
    tmpdir = tempfile.mkdtemp()
    server = ContextPortalSPARCServer(workspace_dir=tmpdir)
    c = server._conn.cursor()
    try:
        c.execute("DROP TABLE phases")
        server._conn.commit()
    finally:
        c.close()
    with pytest.raises(DatabaseQueryError):
        server.get_current_phase()
    server.close()
