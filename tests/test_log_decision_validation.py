import tempfile
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "sparc-server"))
from sparc_mcp_wrapper import (
    SPARCMCPServer,
    InputValidationError,
    DecisionLoggingError,
)
from specialized_mcp_server import ContextPortalSPARCServer

def _setup_wrapper() -> SPARCMCPServer:
    wrapper = SPARCMCPServer()
    tmpdir = tempfile.mkdtemp()
    wrapper.context_server = ContextPortalSPARCServer(workspace_dir=tmpdir)
    return wrapper

def test_log_decision_valid() -> None:
    wrapper = _setup_wrapper()
    result = wrapper._log_decision_tool({
        "summary": "Test",
        "rationale": "Because",
        "tags": ["tag1"],
    })
    assert result["logged"] and result["decision_id"] > 0

def test_log_decision_missing_summary() -> None:
    wrapper = _setup_wrapper()
    with pytest.raises(InputValidationError):
        wrapper._log_decision_tool({"summary": " ", "rationale": "Because"})

def test_log_decision_invalid_tags_type() -> None:
    wrapper = _setup_wrapper()
    with pytest.raises(InputValidationError):
        wrapper._log_decision_tool({"summary": "s", "rationale": "r", "tags": "no"})

def test_log_decision_tag_too_long() -> None:
    wrapper = _setup_wrapper()
    long_tag = "a" * 51
    with pytest.raises(InputValidationError):
        wrapper._log_decision_tool({"summary": "s", "rationale": "r", "tags": [long_tag]})

def test_log_decision_too_many_tags() -> None:
    wrapper = _setup_wrapper()
    tags = [str(i) for i in range(21)]
    with pytest.raises(InputValidationError):
        wrapper._log_decision_tool({"summary": "s", "rationale": "r", "tags": tags})

def test_log_decision_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    wrapper = _setup_wrapper()
    def boom(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(wrapper.context_server, "log_decision", boom)
    with pytest.raises(DecisionLoggingError):
        wrapper._log_decision_tool({"summary": "s", "rationale": "r"})
