import sqlite3
from datetime import datetime, timezone

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'viewer',
    email TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    size_class TEXT NOT NULL DEFAULT 'mittel',
    status TEXT NOT NULL DEFAULT 'laufend',
    priority TEXT NOT NULL DEFAULT 'normal',
    location TEXT NOT NULL DEFAULT '',
    manager TEXT NOT NULL DEFAULT '',
    start_plan TEXT NOT NULL,
    end_plan TEXT NOT NULL,
    end_forecast TEXT,
    budget REAL NOT NULL DEFAULT 0,
    progress_plan REAL NOT NULL DEFAULT 0,
    progress_actual REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    start_plan TEXT NOT NULL,
    end_plan TEXT NOT NULL,
    start_actual TEXT,
    end_actual TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    date_plan TEXT NOT NULL,
    date_actual TEXT,
    weight REAL NOT NULL DEFAULT 1.0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cost_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    amount_plan REAL NOT NULL DEFAULT 0,
    amount_actual REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hours_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    employee TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT '',
    task TEXT NOT NULL DEFAULT '',
    hours_plan REAL NOT NULL DEFAULT 0,
    hours_actual REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

TABLES = ["users", "projects", "phases", "milestones", "cost_entries", "hours_entries"]


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class CentralDB:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        first_run = self.conn.execute(
            "SELECT value FROM settings WHERE key='seeded'"
        ).fetchone() is None
        if first_run:
            from server import seed

            seed.run(self)
            self.conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('seeded', ?)",
                (utcnow(),),
            )
            self.conn.commit()
        if self.conn.execute("SELECT value FROM settings WHERE key='schema_version'").fetchone() is None:
            self.conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            self.conn.commit()

    def fetch_updated(self, table, since):
        rows = self.conn.execute(
            f"SELECT * FROM {table} WHERE updated_at > ?", (since,)
        ).fetchall()
        return [dict(r) for r in rows]
