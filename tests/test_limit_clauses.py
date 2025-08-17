import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "sparc-server"))
from specialized_mcp_server import ContextPortalSPARCServer


def _server() -> ContextPortalSPARCServer:
    tmpdir = tempfile.mkdtemp()
    return ContextPortalSPARCServer(workspace_dir=tmpdir)


def test_get_progress_limit_parameterized() -> None:
    server = _server()
    server.log_progress("desc1", "open")
    server.log_progress("desc2", "open")
    rows = server.get_progress(limit=1)
    assert len(rows) == 1
    with pytest.raises(ValueError):
        server.get_progress(limit="1; DROP TABLE progress")


def test_get_system_patterns_limit_parameterized() -> None:
    server = _server()
    server.log_system_pattern("p1", "d1")
    server.log_system_pattern("p2", "d2")
    rows = server.get_system_patterns(limit=1)
    assert len(rows) == 1
    with pytest.raises(ValueError):
        server.get_system_patterns(limit="1; DROP TABLE system_patterns")
