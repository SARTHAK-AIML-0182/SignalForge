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
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id) ON DELETE CASCADE
            );
            """)

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
    finally:
        conn.close()
