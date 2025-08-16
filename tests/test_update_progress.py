import pathlib
import sqlite3
import sys
import tempfile

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "sparc-server"))

from specialized_mcp_server import (
    ContextPortalSPARCServer,
    DatabaseUpdateError,
)


def _server() -> ContextPortalSPARCServer:
    tmpdir = tempfile.mkdtemp()
    return ContextPortalSPARCServer(workspace_dir=tmpdir)


def test_update_progress_success() -> None:
    server = _server()
    pid = server.log_progress(description="init", status="pending")
    server.update_progress(pid, status="done", description="finished")
    row = server.get_progress(limit=1)[0]
    assert row["status"] == "done"
    assert row["description"] == "finished"


def test_update_progress_no_fields() -> None:
    server = _server()
    pid = server.log_progress(description="x", status="pending")
    with pytest.raises(ValueError):
        server.update_progress(pid)


def test_update_progress_not_found() -> None:
    server = _server()
    with pytest.raises(DatabaseUpdateError):
        server.update_progress(999, status="done")


def test_update_progress_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _server()
    pid = server.log_progress(description="y", status="pending")
    server._conn.close()
    with pytest.raises(DatabaseUpdateError):
        server.update_progress(pid, status="done")
