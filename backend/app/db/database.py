import os
import sqlite3
from pathlib import Path
from typing import Optional, Union

from app.core.config import settings


def get_db_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve database path. Absolute paths or :memory: remain as-is."""
    if custom_path is not None:
        target = Path(custom_path)
    else:
        target = Path(settings.DB_PATH)

    if str(target) == ":memory:" or target.is_absolute():
        return target

    # Resolve relative paths against backend directory
    backend_dir = Path(__file__).resolve().parent.parent.parent
    full_path = (backend_dir / target).resolve()
    return full_path


def get_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Create and configure a SQLite connection."""
    resolved_path = get_db_path(db_path)
    
    if str(resolved_path) != ":memory:":
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(resolved_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    if str(resolved_path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize database tables and schema."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                persona_name TEXT NOT NULL,
                persona_domain TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                initialized_at TEXT NOT NULL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                topic_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                source_url TEXT,
                source_name TEXT,
                discovered_at TEXT NOT NULL,
                editorial_score REAL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'discovered',
                rationale TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id) ON DELETE CASCADE
            );
            """)

            # Ensure rationale column exists on existing topics tables
            cursor = conn.execute("PRAGMA table_info(topics);")
            columns = [row["name"] for row in cursor.fetchall()]
            if "rationale" not in columns:
                conn.execute("ALTER TABLE topics ADD COLUMN rationale TEXT;")

            conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                topic_id TEXT,
                text TEXT NOT NULL,
                rationale TEXT,
                sources TEXT NOT NULL DEFAULT '[]',
                editorial_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES topics (topic_id) ON DELETE SET NULL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS research (
                research_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                topic_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                confidence REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES topics (topic_id) ON DELETE CASCADE
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'web',
                title TEXT NOT NULL,
                retrieved_at TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                FOREIGN KEY (research_id) REFERENCES research (research_id) ON DELETE CASCADE
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                workflow_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'RUNNING',
                started_at TEXT NOT NULL,
                completed_at TEXT,
                is_successful INTEGER NOT NULL DEFAULT 0,
                halted_at_stage TEXT,
                rationale TEXT,
                selected_topic_ids TEXT NOT NULL DEFAULT '[]',
                research_ids TEXT NOT NULL DEFAULT '[]',
                draft_ids TEXT NOT NULL DEFAULT '[]',
                publication_ids TEXT NOT NULL DEFAULT '[]',
                traceability TEXT NOT NULL DEFAULT '{}',
                policy TEXT NOT NULL DEFAULT '{}',
                governance TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id) ON DELETE CASCADE
            );
            """)

            # Ensure policy & governance columns exist on existing workflows tables
            cursor = conn.execute("PRAGMA table_info(workflows);")
            wf_columns = [row["name"] for row in cursor.fetchall()]
            if "policy" not in wf_columns:
                conn.execute("ALTER TABLE workflows ADD COLUMN policy TEXT DEFAULT '{}';")
            if "governance" not in wf_columns:
                conn.execute("ALTER TABLE workflows ADD COLUMN governance TEXT DEFAULT '{}';")

            conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_stages (
                stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                stage_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                is_successful INTEGER NOT NULL DEFAULT 0,
                rationale TEXT,
                entity_ids TEXT NOT NULL DEFAULT '{}',
                metadata TEXT NOT NULL DEFAULT '{}',
                stage_order INTEGER NOT NULL,
                FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id) ON DELETE CASCADE
            );
            """)
    finally:
        conn.close()
