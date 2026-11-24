import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from server.database import TABLES, utcnow

CACHE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT,
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
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

EDITABLE = {
    "projects": {"id", "code", "name", "description", "size_class", "status", "priority",
                 "location", "manager", "start_plan", "end_plan", "end_forecast", "budget",
                 "progress_plan", "progress_actual"},
    "phases": {"id", "project_id", "name", "start_plan", "end_plan", "start_actual", "end_actual", "sort_order"},
    "milestones": {"id", "project_id", "name", "date_plan", "date_actual", "weight"},
    "cost_entries": {"id", "project_id", "date", "category", "description", "amount_plan", "amount_actual"},
    "hours_entries": {"id", "project_id", "date", "employee", "role", "task", "hours_plan", "hours_actual"},
    "users": {"id", "username", "full_name", "email", "role", "active"},
}


class LocalDB:
    def __init__(self, path=None):
        if path is None:
            root = os.path.expanduser("~/.projectdash")
            os.makedirs(root, exist_ok=True)
            path = os.path.join(root, "cache.db")
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(CACHE_SCHEMA)
        self.conn.commit()

    def get_meta(self, key, default=None):
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_meta(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?,?)", (key, value))
        self.conn.commit()

    def full_sync(self, payload):
        for table, rows in payload["data"].items():
            for row in rows:
                self.upsert(table, row)
        self.set_meta("last_sync", payload["server_time"])
        self.conn.commit()

    def upsert(self, table, row):
        fields = EDITABLE[table] | {"updated_at"}
        if table == "users":
            fields = fields | {"password_hash"}
        clean = {k: v for k, v in row.items() if k in fields}
        existing = self.conn.execute(f"SELECT id FROM {table} WHERE id=?", (row.get("id"),)).fetchone()
        if existing:
            sets = ", ".join(f"{k}=?" for k in clean)
            self.conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", list(clean.values()) + [row["id"]])
        else:
            cols = ", ".join(clean)
            marks = ", ".join("?" for _ in clean)
            self.conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", list(clean.values()))

    def apply(self, table, rows):
        now = utcnow()
        accepted = []
        for row in rows:
            rid = row.get("id")
            clean = {k: v for k, v in row.items() if k in EDITABLE[table]}
            if rid:
                sets = ", ".join(f"{k}=?" for k in clean)
                self.conn.execute(f"UPDATE {table} SET {sets}, updated_at=? WHERE id=?",
                                  list(clean.values()) + [now, rid])
                accepted.append(rid)
            else:
                cols = ", ".join(list(clean) + ["updated_at"])
                marks = ", ".join("?" * (len(clean) + 1))
                cur = self.conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})",
                                        list(clean.values()) + [now])
                accepted.append(cur.lastrowid)
        self.conn.commit()
        return accepted

    def delete(self, table, row_id):
        self.conn.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))
        self.conn.commit()

    def rows(self, table, where="", params=()):
        return [dict(r) for r in self.conn.execute(f"SELECT * FROM {table} {where}", params)]

    def projects(self):
        return self.rows("projects")

    def project(self, pid):
        r = self.conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

    def phases(self, pid):
        return self.rows("phases", "WHERE project_id=? ORDER BY sort_order", (pid,))

    def milestones(self, pid):
        return self.rows("milestones", "WHERE project_id=? ORDER BY date_plan", (pid,))

    def costs(self, pid):
        return self.rows("cost_entries", "WHERE project_id=? ORDER BY date, category", (pid,))

    def hours(self, pid):
        return self.rows("hours_entries", "WHERE project_id=? ORDER BY date, employee", (pid,))

    def users(self):
        return [dict(r) for r in self.conn.execute(
            "SELECT id, username, full_name, email, role, active, updated_at FROM users ORDER BY username")]

    def has_data(self):
        return self.conn.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"] > 0
