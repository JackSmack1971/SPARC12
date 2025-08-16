"""
specialized_mcp_server.py
==========================

This module implements a specialized Model Context Protocol (MCP) server that
combines the database‑backed knowledge graph of the Context Portal (ConPort)
with the 12‑phase methodology found in the SPARC12 framework.  ConPort
provides a memory bank for project context, including structured storage for
decisions, progress and system patterns, along with a SQLite backend and
semantic search using vector embeddings【586346173518336†L48-L63】.  SPARC12
extends this idea by introducing a 12‑phase development lifecycle, custom
AI modes and a persistent memory bank to track architectural decisions and
project state【319263862950279†L24-L33】.

The goal of this server is to unify these two systems.  It offers:

* **Phase‑aware context storage** – Each record in the database is tagged
  with a SPARC phase, allowing the server to manage the current phase and
  automatically transition to the next stage when all deliverables are
  completed.
* **Semantic search** – Project artefacts (decisions, progress, system
  patterns and custom data) are indexed using TF‑IDF vectors.  A simple
  retrieval function computes cosine similarity across all stored items to
  support natural‑language queries.  Although this implementation uses
  TF‑IDF rather than deep language models, it still provides a basic
  semantic search capability without external dependencies.
* **RAG‑powered assistance** – The `rag_assist` method retrieves the most
  relevant context items for a given query and SPARC mode.  Downstream
  agents can use this to augment their responses.
* **File/database synchronisation** – Hooks are provided to import data
  from a SPARC12 memory bank (a directory of markdown files) into the
  SQLite database and export database entries back to disk.  This keeps
  the file based memory in sync with the database‑backed knowledge graph.

This module does not implement a network server.  Instead it exposes a
``ContextPortalSPARCServer`` class with methods mirroring the ConPort
tool APIs.  Developers can integrate this class into an application or
extend it into a service (e.g. using `asyncio` or `FastAPI`) as needed.

Note: For brevity and clarity this implementation uses simplified error
handling and does not enforce concurrency limits.  It is intended as a
starting point rather than a production‑ready service.
"""

import json
import os
import sqlite3
import datetime
import logging
from dataclasses import dataclass, asdict
from types import TracebackType
from typing import Any, Dict, List, Optional, Tuple, Type

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class DatabaseUpdateError(Exception):
    """Raised when a database update operation fails."""


class DatabaseQueryError(Exception):
    """Raised when a database query operation fails."""


class DatabaseConnectionError(Exception):
    """Raised when establishing a database connection fails."""


def _current_timestamp() -> str:
    """Return the current UTC timestamp as ISO8601 string."""
    return datetime.datetime.utcnow().isoformat() + "Z"


@dataclass
class Phase:
    name: str
    status: str = "pending"
    completion_date: Optional[str] = None
    deliverables: Optional[Dict[str, Any]] = None


class ContextPortalSPARCServer:
    """Combine ConPort's knowledge graph with SPARC12 methodology.

    The class encapsulates a SQLite database that stores product context,
    active context, decisions, progress entries, system patterns and custom
    data.  Each record can be associated with a SPARC phase.  The server
    exposes methods similar to the ConPort tools while adding phase
    management and semantic search.
    """

    PHASE_SEQUENCE = [
        "research", "specification", "design", "architecture",
        "implementation", "testing", "security review", "qa validation",
        "integration", "deployment", "documentation", "project complete",
    ]

    def __init__(self, workspace_dir: str, db_path: Optional[str] = None) -> None:
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.db_path = db_path or os.path.join(
            self.workspace_dir, "context_portal", "context.db"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Establish the SQLite connection with safety checks."""
        if self._conn:
            return
        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._ensure_tables()
            self._initialize_phases()
        except sqlite3.Error as exc:
            if self._conn:
                try:
                    self._conn.close()
                except sqlite3.Error:
                    pass
                finally:
                    self._conn = None
            raise DatabaseConnectionError(str(exc)) from exc

    def __enter__(self) -> "ContextPortalSPARCServer":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the database connection safely."""
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            finally:
                self._conn = None

    def __del__(self) -> None:
        self.close()

    def _ensure_tables(self) -> None:
        """Create tables if they don't exist."""
        c = self._conn.cursor()
        # Product and active context tables hold a single JSON blob
        c.execute(
            """CREATE TABLE IF NOT EXISTS product_context (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS active_context (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT
            )"""
        )
        # Phase tracking table
        c.execute(
            """CREATE TABLE IF NOT EXISTS phases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                status TEXT,
                completion_date TEXT,
                deliverables TEXT
            )"""
        )
        # Generic item tables
        c.execute(
            """CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT,
                rationale TEXT,
                tags TEXT,
                timestamp TEXT,
                phase_name TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                status TEXT,
                timestamp TEXT,
                parent_id INTEGER,
                phase_name TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS system_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                tags TEXT,
                timestamp TEXT,
                phase_name TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS custom_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                key TEXT,
                value TEXT,
                timestamp TEXT,
                phase_name TEXT
            )"""
        )
        self._conn.commit()

    def _initialize_phases(self) -> None:
        """Ensure all phases exist in the phases table with default status."""
        c = self._conn.cursor()
        for phase in self.PHASE_SEQUENCE:
            c.execute(
                "INSERT OR IGNORE INTO phases (name, status) VALUES (?, ?)",
                (phase, "pending"),
            )
        # Ensure there is at least one current phase.  If all phases are
        # pending, set the first phase to active.
        c.execute("SELECT COUNT(*) as cnt FROM phases WHERE status = 'active'")
        if c.fetchone()["cnt"] == 0:
            c.execute(
                "UPDATE phases SET status = 'active' WHERE name = ?",
                (self.PHASE_SEQUENCE[0],),
            )
        self._conn.commit()

    # Product context methods
    def get_product_context(self) -> Optional[Dict[str, Any]]:
        c = self._conn.cursor()
        row = c.execute("SELECT data FROM product_context WHERE id = 1").fetchone()
        if row and row["data"]:
            return json.loads(row["data"])
        return None

    def update_product_context(
        self,
        content: Optional[Dict[str, Any]] = None,
        patch_content: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update product context.  Accepts either a full replacement
        (`content`) or a partial update (`patch_content`).  If both are
        provided, patch takes precedence for overlapping keys.
        """
        c = self._conn.cursor()
        current = self.get_product_context() or {}
        if content is not None:
            current = content
        if patch_content:
            for k, v in patch_content.items():
                if v == "__DELETE__":
                    current.pop(k, None)
                else:
                    current[k] = v
        data_str = json.dumps(current)
        c.execute(
            "INSERT INTO product_context (id, data) VALUES (1, ?)\n"
            "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
            (data_str,),
        )
        self._conn.commit()

    # Active context methods
    def get_active_context(self) -> Optional[Dict[str, Any]]:
        c = self._conn.cursor()
        row = c.execute("SELECT data FROM active_context WHERE id = 1").fetchone()
        if row and row["data"]:
            return json.loads(row["data"])
        return None

    def update_active_context(
        self,
        content: Optional[Dict[str, Any]] = None,
        patch_content: Optional[Dict[str, Any]] = None,
    ) -> None:
        current = self.get_active_context() or {}
        if content is not None:
            current = content
        if patch_content:
            for k, v in patch_content.items():
                if v == "__DELETE__":
                    current.pop(k, None)
                else:
                    current[k] = v
        data_str = json.dumps(current)
        c = self._conn.cursor()
        c.execute(
            "INSERT INTO active_context (id, data) VALUES (1, ?)\n"
            "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
            (data_str,),
        )
        self._conn.commit()

    # Decision logging methods
    def log_decision(
        self, summary: str, rationale: str, tags: Optional[List[str]] = None
    ) -> int:
        c = self._conn.cursor()
        phase = self.get_current_phase()
        timestamp = _current_timestamp()
        c.execute(
            "INSERT INTO decisions (summary, rationale, tags, timestamp, phase_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (summary, rationale, ",".join(tags or []), timestamp, phase),
        )
        self._conn.commit()
        return c.lastrowid

    def get_decisions(
        self,
        limit: Optional[int] = None,
        tags_filter_include_all: Optional[List[str]] = None,
        tags_filter_include_any: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        c = self._conn.cursor()
        query = "SELECT * FROM decisions"
        params: List[Any] = []
        conditions: List[str] = []
        if tags_filter_include_all:
            for tag in tags_filter_include_all:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
        if tags_filter_include_any:
            tags_any = [f"tags LIKE ?" for _ in tags_filter_include_any]
            conditions.append("(" + " OR ".join(tags_any) + ")")
            params.extend([f"%{tag}%" for tag in tags_filter_include_any])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = c.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def search_decisions_fts(self, query_term: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform a simple full‑text search across decisions' summary
        and rationale fields."""
        c = self._conn.cursor()
        pattern = f"%{query_term}%"
        rows = c.execute(
            "SELECT * FROM decisions WHERE summary LIKE ? OR rationale LIKE ? ORDER BY id DESC LIMIT ?",
            (pattern, pattern, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def delete_decision_by_id(self, decision_id: int) -> None:
        c = self._conn.cursor()
        c.execute("DELETE FROM decisions WHERE id = ?", (decision_id,))
        self._conn.commit()

    # Progress tracking methods
    def log_progress(
        self,
        description: str,
        status: str,
        parent_id: Optional[int] = None,
    ) -> int:
        c = self._conn.cursor()
        phase = self.get_current_phase()
        timestamp = _current_timestamp()
        c.execute(
            "INSERT INTO progress (description, status, timestamp, parent_id, phase_name)"
            " VALUES (?, ?, ?, ?, ?)",
            (description, status, timestamp, parent_id, phase),
        )
        self._conn.commit()
        return c.lastrowid

    def get_progress(
        self,
        status_filter: Optional[str] = None,
        parent_id_filter: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        c = self._conn.cursor()
        query = "SELECT * FROM progress"
        conditions: List[str] = []
        params: List[Any] = []
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        if parent_id_filter is not None:
            conditions.append("parent_id = ?")
            params.append(parent_id_filter)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = c.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def update_progress(self, progress_id: int, status: Optional[str] = None,
                        description: Optional[str] = None,
                        parent_id: Optional[int] = None) -> None:
        if not any([status is not None, description is not None, parent_id is not None]):
            raise ValueError("At least one field must be provided for update")
        c = None
        try:
            with self._conn:
                c = self._conn.cursor()
                exists = c.execute("SELECT 1 FROM progress WHERE id = ?", (progress_id,)).fetchone()
                if not exists: raise DatabaseUpdateError(f"Progress item with id {progress_id} not found")
                update_fields, params = [], []
                if status is not None: update_fields.append("status = ?"); params.append(status)
                if description is not None: update_fields.append("description = ?"); params.append(description)
                if parent_id is not None: update_fields.append("parent_id = ?"); params.append(parent_id)
                params.append(progress_id)
                c.execute(
                    f"UPDATE progress SET {', '.join(update_fields)} WHERE id = ?",  # nosec B608
                    params,
                )
        except sqlite3.DatabaseError as exc:
            raise DatabaseUpdateError(f"Failed to update progress {progress_id}: {exc}") from exc
        finally:
            if c: c.close()

    def delete_progress_by_id(self, progress_id: int) -> None:
        c = self._conn.cursor()
        c.execute("DELETE FROM progress WHERE id = ?", (progress_id,))
        self._conn.commit()

    # System pattern methods
    def log_system_pattern(
        self, name: str, description: str, tags: Optional[List[str]] = None
    ) -> int:
        c = self._conn.cursor()
        phase = self.get_current_phase()
        timestamp = _current_timestamp()
        c.execute(
            "INSERT INTO system_patterns (name, description, tags, timestamp, phase_name)"
            " VALUES (?, ?, ?, ?, ?)",
            (name, description, ",".join(tags or []), timestamp, phase),
        )
        self._conn.commit()
        return c.lastrowid

    def get_system_patterns(
        self,
        tags_filter_include_all: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        c = self._conn.cursor()
        query = "SELECT * FROM system_patterns"
        conditions: List[str] = []
        params: List[Any] = []
        if tags_filter_include_all:
            for tag in tags_filter_include_all:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = c.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def delete_system_pattern_by_id(self, pattern_id: int) -> None:
        c = self._conn.cursor()
        c.execute("DELETE FROM system_patterns WHERE id = ?", (pattern_id,))
        self._conn.commit()

    # Custom data methods
    def log_custom_data(
        self,
        category: str,
        key: str,
        value: Any,
    ) -> int:
        c = self._conn.cursor()
        phase = self.get_current_phase()
        timestamp = _current_timestamp()
        c.execute(
            "INSERT INTO custom_data (category, key, value, timestamp, phase_name)"
            " VALUES (?, ?, ?, ?, ?)",
            (category, key, json.dumps(value), timestamp, phase),
        )
        self._conn.commit()
        return c.lastrowid

    def get_custom_data(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        c = self._conn.cursor()
        row = c.execute(
            "SELECT * FROM custom_data WHERE category = ? AND key = ? ORDER BY id DESC",
            (category, key),
        ).fetchone()
        if row:
            result = dict(row)
            result["value"] = json.loads(result["value"])
            return result
        return None

    def delete_custom_data(self, category: str, key: str) -> None:
        c = self._conn.cursor()
        c.execute(
            "DELETE FROM custom_data WHERE category = ? AND key = ?",
            (category, key),
        )
        self._conn.commit()

    def search_custom_data_value_fts(
        self,
        query_term: str,
        category_filter: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        pattern = f"%{query_term}%"
        c = self._conn.cursor()
        try:
            query = "SELECT * FROM custom_data WHERE value LIKE ?"
            params: List[Any] = [pattern]
            if category_filter:
                query += " AND category = ?"
                params.append(category_filter)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            rows = c.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.DatabaseError as exc:
            raise DatabaseQueryError("Failed to search custom data") from exc

    # Phase management
    def get_current_phase(self) -> str:
        c = self._conn.cursor()
        c.row_factory = sqlite3.Row
        try:
            row = c.execute(
                "SELECT name FROM phases WHERE status = 'active' LIMIT 1"
            ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise DatabaseQueryError("Failed to fetch current phase") from exc
        finally:
            c.close()
        if row:
            return row["name"]
        return self.PHASE_SEQUENCE[0]

    def transition_to_next_phase(self) -> None:
        """Mark the current phase as complete and activate the next phase."""
        c = self._conn.cursor()
        current = self.get_current_phase()
        idx = self.PHASE_SEQUENCE.index(current)
        # Mark current phase complete
        c.execute(
            "UPDATE phases SET status = 'complete', completion_date = ? WHERE name = ?",
            (_current_timestamp(), current),
        )
        if idx + 1 < len(self.PHASE_SEQUENCE):
            next_phase = self.PHASE_SEQUENCE[idx + 1]
            c.execute(
                "UPDATE phases SET status = 'active' WHERE name = ?",
                (next_phase,),
            )
        self._conn.commit()

    # Semantic search across all items
    def _collect_texts(self) -> Tuple[List[str], List[Tuple[str, int]]]:
        """Gather all textual fields across supported tables.

        Returns a tuple of (list of documents, list of identifiers).
        Each identifier is a tuple (table_name, id).
        """
        docs: List[str] = []
        ids: List[Tuple[str, int]] = []
        c = self._conn.cursor()
        # decisions: summary + rationale
        for row in c.execute("SELECT id, summary, rationale FROM decisions"):
            docs.append(f"decision: {row['summary']}. {row['rationale']}")
            ids.append(("decisions", row["id"]))
        # progress: description
        for row in c.execute("SELECT id, description FROM progress"):
            docs.append(f"progress: {row['description']}")
            ids.append(("progress", row["id"]))
        # system patterns: name + description
        for row in c.execute("SELECT id, name, description FROM system_patterns"):
            docs.append(f"system pattern: {row['name']}. {row['description']}")
            ids.append(("system_patterns", row["id"]))
        # custom data: category/key + value string
        for row in c.execute("SELECT id, category, key, value FROM custom_data"):
            try:
                value_str = json.loads(row["value"])
                if not isinstance(value_str, str):
                    value_str = json.dumps(value_str)
            except Exception:
                value_str = row["value"]
            docs.append(
                f"custom data ({row['category']}/{row['key']}): {value_str}"
            )
            ids.append(("custom_data", row["id"]))
        return docs, ids

    def semantic_search(
        self,
        query_text: str,
        top_k: int = 5,
        filter_item_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search over all stored items.

        It builds a TF‑IDF matrix on demand and returns the top_k items
        most similar to the query.  Optionally restricts results to certain
        table names ("decisions", "progress", "system_patterns", "custom_data").
        """
        docs, ids = self._collect_texts()
        if not docs:
            return []
        vectorizer = TfidfVectorizer(stop_words="english")
        X = vectorizer.fit_transform(docs)
        query_vec = vectorizer.transform([query_text])
        sims = cosine_similarity(query_vec, X).flatten()
        # Get indices of top_k sims
        top_indices = sims.argsort()[::-1]
        results = []
        c = self._conn.cursor()
        for idx in top_indices:
            table_name, item_id = ids[idx]
            if filter_item_types and table_name not in filter_item_types:
                continue
            if table_name == "decisions":
                row = c.execute("SELECT * FROM decisions WHERE id = ?", (item_id,)).fetchone()
            elif table_name == "progress":
                row = c.execute("SELECT * FROM progress WHERE id = ?", (item_id,)).fetchone()
            elif table_name == "system_patterns":
                row = c.execute(
                    "SELECT * FROM system_patterns WHERE id = ?", (item_id,)
                ).fetchone()
            else:  # custom_data
                row = c.execute(
                    "SELECT * FROM custom_data WHERE id = ?", (item_id,)
                ).fetchone()
                if row:
                    row = dict(row)
                    row["value"] = json.loads(row["value"])
            if row:
                result = dict(row)
                result["item_type"] = table_name
                results.append(result)
            if len(results) >= top_k:
                break
        return results

    # RAG assistance
    def rag_assist(
        self, query: str, mode: Optional[str] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a given query and optional SPARC mode.

        The mode parameter can be used to bias the search toward certain
        item types.  For example, an architect might favour decisions and
        system patterns.  The default returns results across all types.
        """
        type_map = {
            "sparc-specification-writer": ["decisions"],
            "sparc-domain-intelligence": ["custom_data", "decisions"],
            "sparc-architect": ["decisions", "system_patterns"],
            "sparc-code-implementer": ["progress", "system_patterns"],
            "sparc-security-reviewer": ["custom_data", "system_patterns"],
            "sparc-qa-analyst": ["progress"],
        }
        filter_types = type_map.get(mode, None)
        return self.semantic_search(query_text=query, top_k=top_k, filter_item_types=filter_types)

    # File/database synchronisation
    def sync_from_memory_bank(self, memory_bank_dir: str) -> None:
        """Import context from a SPARC12 memory bank directory.

        This method scans the provided memory_bank_dir for markdown files and
        updates the database accordingly.  It looks for decisions in
        ``memory-bank/context/`` (files ending in "-decisions.md"), progress
        in ``memory-bank/phases/`` (files containing bullet lists of tasks),
        and system patterns in ``memory-bank/context/`` (files ending in
        "-patterns.md").  Custom data can be imported from
        ``memory-bank/context/*.json`` files.  The parser is intentionally
        simplistic; more sophisticated parsing can be added as needed.
        """
        mb_path = os.path.abspath(memory_bank_dir)
        if not os.path.isdir(mb_path):
            raise FileNotFoundError(f"Memory bank directory not found: {mb_path}")
        # Import decisions
        decisions_dir = os.path.join(mb_path, "context")
        if os.path.isdir(decisions_dir):
            for filename in os.listdir(decisions_dir):
                full = os.path.join(decisions_dir, filename)
                if filename.endswith("-decisions.md") and os.path.isfile(full):
                    with open(full, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("- "):
                                # Expect format: - Summary: rationale (tags)
                                content = line[2:].strip()
                                parts = content.split(";")
                                summary = parts[0].strip()
                                rationale = parts[1].strip() if len(parts) > 1 else ""
                                tags = []
                                # Extract tags within parentheses at end
                                if parts and parts[-1].strip().startswith("(") and parts[-1].strip().endswith(")"):
                                    tag_str = parts[-1].strip()[1:-1]
                                    tags = [t.strip() for t in tag_str.split(",") if t.strip()]
                                self.log_decision(summary=summary, rationale=rationale, tags=tags)
        # Import progress
        phases_dir = os.path.join(mb_path, "phases")
        if os.path.isdir(phases_dir):
            for filename in os.listdir(phases_dir):
                full = os.path.join(phases_dir, filename)
                if filename.endswith("-status.md") and os.path.isfile(full):
                    with open(full, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("- "):
                                # Expect format: - [status] description
                                content = line[2:]
                                if content.startswith("["):
                                    end_bracket = content.find("]")
                                    if end_bracket != -1:
                                        status = content[1:end_bracket]
                                        description = content[end_bracket+1:].strip()
                                        self.log_progress(description=description, status=status)
        # Import system patterns
        if os.path.isdir(decisions_dir):
            for filename in os.listdir(decisions_dir):
                full = os.path.join(decisions_dir, filename)
                if filename.endswith("-patterns.md") and os.path.isfile(full):
                    with open(full, "r", encoding="utf-8") as f:
                        current_name = None
                        desc_lines: List[str] = []
                        for line in f:
                            if line.startswith("## "):
                                # Save previous pattern
                                if current_name is not None:
                                    description = "\n".join(desc_lines).strip()
                                    self.log_system_pattern(name=current_name, description=description)
                                current_name = line[3:].strip()
                                desc_lines = []
                            else:
                                desc_lines.append(line.rstrip())
                        # Save last pattern
                        if current_name:
                            description = "\n".join(desc_lines).strip()
                            self.log_system_pattern(name=current_name, description=description)
        # Import custom data from JSON
        for root, _, files in os.walk(os.path.join(mb_path, "context")):
            for filename in files:
                if filename.endswith(".json"):
                    full = os.path.join(root, filename)
                    with open(full, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except (json.JSONDecodeError, OSError) as exc:
                            logging.warning("Error processing %s: %s", filename, exc)
                            continue
                        category = os.path.splitext(filename)[0]
                        for key, value in data.items():
                            self.log_custom_data(category=category, key=key, value=value)

    def sync_to_memory_bank(self, memory_bank_dir: str) -> None:
        """Export database entries back into a SPARC12 memory bank structure.

        This method writes decisions, progress and system patterns into
        markdown files under the given memory_bank_dir.  Existing files
        will be overwritten.  Custom data is saved as JSON files.
        """
        mb_path = os.path.abspath(memory_bank_dir)
        os.makedirs(mb_path, exist_ok=True)
        # Write decisions
        ctx_dir = os.path.join(mb_path, "context")
        os.makedirs(ctx_dir, exist_ok=True)
        decisions = self.get_decisions()
        if decisions:
            dec_file = os.path.join(ctx_dir, "imported-decisions.md")
            with open(dec_file, "w", encoding="utf-8") as f:
                f.write("# Imported Decisions\n\n")
                for dec in decisions:
                    tags = f" ({dec['tags']})" if dec.get("tags") else ""
                    f.write(f"- {dec['summary']}; {dec['rationale']}{tags}\n")
        # Write progress
        phases_dir = os.path.join(mb_path, "phases")
        os.makedirs(phases_dir, exist_ok=True)
        prog = self.get_progress()
        if prog:
            prog_file = os.path.join(phases_dir, "imported-status.md")
            with open(prog_file, "w", encoding="utf-8") as f:
                f.write("# Imported Progress\n\n")
                for pr in prog:
                    f.write(f"- [{pr['status']}] {pr['description']}\n")
        # Write system patterns
        patterns = self.get_system_patterns()
        if patterns:
            pat_file = os.path.join(ctx_dir, "imported-patterns.md")
            with open(pat_file, "w", encoding="utf-8") as f:
                for pat in patterns:
                    f.write(f"## {pat['name']}\n{pat['description']}\n\n")
        # Write custom data as JSON
        c = self._conn.cursor()
        rows = c.execute("SELECT category, key, value FROM custom_data").fetchall()
        custom_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            cat = row["category"]
            key = row["key"]
            value = json.loads(row["value"])
            custom_map.setdefault(cat, {})[key] = value
        for category, data in custom_map.items():
            out_file = os.path.join(ctx_dir, f"{category}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ContextPortalSPARCServer CLI")
    parser.add_argument(
        "workspace_dir",
        type=str,
        help="Path to the root of your project (workspace). This is used to locate the context portal database.",
    )
    parser.add_argument(
        "--action",
        type=str,
        default="status",
        choices=[
            "status",
            "transition",
            "rag",
            "import",
            "export",
        ],
        help="Action to perform: 'status' (show current phase), 'transition' (move to next phase), 'rag' (RAG search), 'import' (sync from memory bank), 'export' (sync to memory bank)",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query text for rag action",
    )
    parser.add_argument(
        "--mode",
        type=str,
        help="SPARC mode for rag action",
    )
    parser.add_argument(
        "--memory-bank",
        type=str,
        help="Path to memory-bank directory for import/export",
    )
    args = parser.parse_args()

    server = ContextPortalSPARCServer(workspace_dir=args.workspace_dir)
    try:
        if args.action == "status":
            print("Current phase:", server.get_current_phase())
        elif args.action == "transition":
            server.transition_to_next_phase()
            print("Transitioned to next phase. Current phase:", server.get_current_phase())
        elif args.action == "rag":
            if not args.query:
                raise SystemExit("--query is required for rag action")
            results = server.rag_assist(query=args.query, mode=args.mode)
            for item in results:
                print(item)
        elif args.action == "import":
            if not args.memory_bank:
                raise SystemExit("--memory-bank is required for import action")
            server.sync_from_memory_bank(args.memory_bank)
            print("Imported memory bank into database.")
        elif args.action == "export":
            if not args.memory_bank:
                raise SystemExit("--memory-bank is required for export action")
            server.sync_to_memory_bank(args.memory_bank)
            print("Exported database to memory bank.")
    finally:
        server.close()