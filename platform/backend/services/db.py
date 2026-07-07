from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional


class Database:
    def __init__(self, db_path: Optional[str] = None) -> None:
        if not db_path:
            db_path = str(Path(__file__).resolve().parent.parent / "data" / "platform.db")
        self.db_path = db_path
        self._local = threading.local()
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = self._connect()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._cursor() as cursor:
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS users_new (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
                    name TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    marker TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    started_at TEXT NOT NULL DEFAULT (datetime('now')),
                    finished_at TEXT,
                    result TEXT,
                    logs TEXT
                );
                """
            )
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [row["name"] for row in cursor.fetchall()]
            if "username" in user_columns and "user_id" not in user_columns:
                cursor.execute(
                    """
                    INSERT INTO users_new (username, password, role, name, phone, email, created_at, updated_at)
                    SELECT username, password, role, '', '', '', created_at, updated_at
                    FROM users
                    """
                )
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_new RENAME TO users")
                cursor.execute(
                    "UPDATE users SET phone = 'user_' || lower(hex(randomblob(4))) || substr(lower(hex(randomblob(2))), 1, 4) WHERE phone = ''"
                )
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone)
                """
            )
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_users_updated_at
                AFTER UPDATE ON users
                FOR EACH ROW
                BEGIN
                    UPDATE users SET updated_at = datetime('now') WHERE user_id = OLD.user_id;
                END;
                """
            )
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute(
                    "INSERT INTO users (username, password, role, name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                    ("admin", "admin123", "admin", "管理员", "13800000000", "admin@example.com"),
                )


db = Database()
