import os
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "sparc-server"))
from specialized_mcp_server import ContextPortalSPARCServer, MemoryBankSyncError


@pytest.fixture
def server(tmp_path):
    srv = ContextPortalSPARCServer(workspace_dir=str(tmp_path))
    yield srv
    srv.close()


def test_sync_from_absolute_path_rejected(server, tmp_path):
    abs_dir = tmp_path / "mb"
    abs_dir.mkdir()
    with pytest.raises(MemoryBankSyncError):
        server.sync_from_memory_bank(str(abs_dir))


def test_sync_from_traversal_rejected(server, tmp_path):
    outside = tmp_path.parent / "outside"
    outside.mkdir()
    rel = os.path.relpath(outside, tmp_path)
    with pytest.raises(MemoryBankSyncError):
        server.sync_from_memory_bank(rel)


def test_sync_to_absolute_path_rejected(server, tmp_path):
    abs_dir = tmp_path / "export"
    with pytest.raises(MemoryBankSyncError):
        server.sync_to_memory_bank(str(abs_dir))


def test_sync_to_traversal_rejected(server, tmp_path):
    outside = tmp_path.parent / "out"
    rel = os.path.relpath(outside, tmp_path)
    with pytest.raises(MemoryBankSyncError):
        server.sync_to_memory_bank(rel)


def test_sync_from_and_to_valid_path(server, tmp_path):
    mb = tmp_path / "mb"
    context = mb / "context"
    phases = mb / "phases"
    context.mkdir(parents=True)
    phases.mkdir()
    (context / "sample-decisions.md").write_text("- summary; rationale\n")
    (phases / "sample-status.md").write_text("- [done] task\n")
    server.sync_from_memory_bank("mb")
    server.sync_to_memory_bank("export")
    assert (tmp_path / "export").is_dir()
