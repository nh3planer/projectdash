import hmac
import os
import secrets
import sqlite3
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server import auth
from server.database import CentralDB, TABLES, utcnow


def _default_db_path():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        env_base = os.environ.get("PROJECTDASH_DB")
        if env_base:
            return env_base
        base = os.path.join(os.path.dirname(__file__), "..")
    return os.path.join(base, "data", "central.db")


def _db_port():
    return int(os.environ.get("PROJECTDASH_PORT", "8750"))


DB_PATH = _default_db_path()
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = CentralDB(DB_PATH)

app = FastAPI(title="ProjectDash Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _secret():
    row = db.conn.execute("SELECT value FROM settings WHERE key='server_secret'").fetchone()
    if row is None:
        value = secrets.token_hex(32)
        db.conn.execute("INSERT INTO settings (key, value) VALUES ('server_secret', ?)", (value,))
        db.conn.commit()
        return value
    return row["value"]


def _sign(username):
    secret = _secret()
    mac = hmac.new(secret.encode(), username.encode(), "sha256").hexdigest()
    return f"{username}:{mac}"


def _user_from_token(token):
    if not token or ":" not in token:
        return None
    username, mac = token.split(":", 1)
    expected = hmac.new(_secret().encode(), username.encode(), "sha256").hexdigest()
    if not hmac.compare_digest(mac, expected):
        return None
    row = db.conn.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone()
    return dict(row) if row else None


async def require_user(request: Request, permission=None, role=None):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = _user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Nicht angemeldet oder Session ungültig")
    perms = auth.permissions_for(user["role"])
    if permission and permission not in perms:
        raise HTTPException(status_code=403, detail=f"Keine Berechtigung: {permission}")
    if role and user["role"] != role:
        raise HTTPException(status_code=403, detail="Rolle erforderlich")
    return user


class LoginRequest(BaseModel):
    username: str
    password: str


class SyncRequest(BaseModel):
    since: str = ""


class PushRequest(BaseModel):
    table: str
    rows: list


class ChangeSet(BaseModel):
    username: str
    full_name: str = ""
    email: str = ""
    role: str
    active: bool = True
    password: str = ""


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@app.get("/health")
def health():
    return {"status": "ok", "time": utcnow()}


@app.post("/login")
def login(req: LoginRequest):
    row = db.conn.execute("SELECT * FROM users WHERE username=?", (req.username,)).fetchone()
    if row is None or not auth.verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Benutzername oder Passwort falsch")
    if not row["active"]:
        raise HTTPException(status_code=403, detail="Benutzer ist deaktiviert")
    return {
        "token": _sign(req.username),
        "user": {
            "id": row["id"], "username": row["username"], "full_name": row["full_name"],
            "email": row["email"], "role": row["role"],
        },
        "permissions": auth.permissions_for(row["role"]),
    }


@app.post("/verify")
async def verify(request: Request):
    user = await require_user(request)
    return {"user": {k: user[k] for k in ("id", "username", "full_name", "email", "role")},
            "permissions": auth.permissions_for(user["role"])}


@app.post("/sync")
async def sync(req: SyncRequest, request: Request):
    user = await require_user(request)
    perms = auth.permissions_for(user["role"])
    data = {}
    for table in TABLES:
        rows = db.fetch_updated(table, req.since or "")
        if table == "users":
            for r in rows:
                r.pop("password_hash", None)
        data[table] = rows
    return {"server_time": utcnow(), "data": data}


PUSHABLE = {
    "projects": "edit_projects",
    "phases": "edit_projects",
    "milestones": "edit_projects",
    "cost_entries": "edit_costs",
    "hours_entries": "edit_hours",
    "users": "manage_users",
}
EDITABLE_FIELDS = {
    "projects": {"code", "name", "description", "size_class", "status", "priority", "location",
                  "manager", "start_plan", "end_plan", "end_forecast", "budget",
                  "progress_plan", "progress_actual"},
    "phases": {"project_id", "name", "start_plan", "end_plan", "start_actual", "end_actual", "sort_order"},
    "milestones": {"project_id", "name", "date_plan", "date_actual", "weight"},
    "cost_entries": {"project_id", "date", "category", "description", "amount_plan", "amount_actual"},
    "hours_entries": {"project_id", "date", "employee", "role", "task", "hours_plan", "hours_actual"},
    "users": {"username", "full_name", "email", "role", "active"},
}


@app.post("/push")
async def push(req: PushRequest, request: Request):
    user = await require_user(request)
    if req.table not in PUSHABLE:
        raise HTTPException(status_code=400, detail=f"Tabelle nicht synchronisierbar: {req.table}")
    required_perm = PUSHABLE[req.table]
    if required_perm not in auth.permissions_for(user["role"]):
        if not (req.table == "hours_entries" and _only_own_hours(req.rows, user)):
            raise HTTPException(status_code=403, detail=f"Keine Berechtigung: {required_perm}")
    fields = EDITABLE_FIELDS[req.table]
    accepted = []
    now = utcnow()
    for row in req.rows:
        rid = row.get("id")
        clean = {k: v for k, v in row.items() if k in fields}
        if req.table == "projects":
            clean.setdefault("progress_plan", 0)
            clean.setdefault("progress_actual", 0)
        if rid:
            sets = ", ".join(f"{k}=?" for k in clean)
            params = list(clean.values()) + [now, rid]
            cur = db.conn.execute(f"UPDATE {req.table} SET {sets}, updated_at=? WHERE id=?", params)
            if cur.rowcount == 0:
                continue
        else:
            cols = ", ".join(clean)
            marks = ", ".join("?" for _ in clean)
            cur = db.conn.execute(
                f"INSERT INTO {req.table} ({cols}, updated_at) VALUES ({marks}, ?)",
                list(clean.values()) + [now],
            )
            rid = cur.lastrowid
        if req.table == "users" and row.get("password"):
            db.conn.execute("UPDATE users SET password_hash=?, updated_at=? WHERE id=?",
                            (auth.hash_password(row["password"]), now, rid))
        accepted.append(rid)
    db.conn.commit()
    return {"accepted_ids": accepted, "server_time": now}


def _only_own_hours(rows, user):
    return all(r.get("employee", "").lower() == user["full_name"].lower() or
               r.get("employee", "").lower() == user["username"].lower() for r in rows)


@app.get("/users")
async def list_users(request: Request):
    await require_user(request, permission="manage_users")
    rows = db.conn.execute(
        "SELECT id, username, full_name, email, role, active, updated_at FROM users"
    ).fetchall()
    return [dict(r) for r in rows]


@app.post("/users")
async def create_user(cs: ChangeSet, request: Request):
    await require_user(request, permission="manage_users")
    if cs.role not in auth.ROLES:
        raise HTTPException(status_code=400, detail=f"Unbekannte Rolle: {cs.role}")
    try:
        db.conn.execute(
            "INSERT INTO users (username, password_hash, full_name, email, role, active, updated_at) VALUES (?,?,?,?,?,?,?)",
            (cs.username, auth.hash_password(cs.password or secrets.token_urlsafe(8)),
             cs.full_name, cs.email, cs.role, int(cs.active), utcnow()),
        )
        db.conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Benutzername existiert bereits")
    return {"status": "created"}


@app.post("/users/{user_id}")
async def update_user(user_id: int, cs: ChangeSet, request: Request):
    await require_user(request, permission="manage_users")
    if cs.role not in auth.ROLES:
        raise HTTPException(status_code=400, detail=f"Unbekannte Rolle: {cs.role}")
    if cs.password:
        db.conn.execute(
            "UPDATE users SET full_name=?, email=?, role=?, active=?, password_hash=?, updated_at=? WHERE id=?",
            (cs.full_name, cs.email, cs.role, int(cs.active), auth.hash_password(cs.password), utcnow(), user_id),
        )
    else:
        db.conn.execute(
            "UPDATE users SET full_name=?, email=?, role=?, active=?, updated_at=? WHERE id=?",
            (cs.full_name, cs.email, cs.role, int(cs.active), utcnow(), user_id),
        )
    db.conn.commit()
    return {"status": "updated"}


@app.post("/password")
async def change_password(req: PasswordChange, request: Request):
    user = await require_user(request)
    if not auth.verify_password(req.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Altes Passwort falsch")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Neues Passwort zu kurz (min. 6 Zeichen)")
    db.conn.execute("UPDATE users SET password_hash=?, updated_at=? WHERE id=?",
                    (auth.hash_password(req.new_password), utcnow(), user["id"]))
    db.conn.commit()
    return {"status": "changed"}


def main():
    import uvicorn
    port = int(sys.argv[1]) if len(sys.argv) > 1 else _db_port()
    print(f"ProjectDash-Server läuft auf Port {port}")
    print(f"Datenbank: {DB_PATH}")
    print("Server mit Strg+C beenden.")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
