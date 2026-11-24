import hashlib
import hmac
import os
import secrets
import sqlite3

ROLES = [
    "admin",
    "management",
    "projektleiter",
    "mitarbeiter",
    "gast",
]

PERMISSIONS = {
    "admin": [
        "view_projects", "edit_projects", "view_costs", "edit_costs",
        "view_hours", "edit_hours", "view_management", "manage_users",
        "import_data", "export_data", "export_pdf",
    ],
    "management": [
        "view_projects", "edit_projects", "view_costs", "edit_costs",
        "view_hours", "view_management", "export_data", "export_pdf",
    ],
    "projektleiter": [
        "view_projects", "edit_projects", "view_costs", "edit_costs",
        "view_hours", "edit_hours", "import_data", "export_data", "export_pdf",
    ],
    "mitarbeiter": [
        "view_projects", "view_hours", "edit_hours",
    ],
    "gast": ["view_projects"],
}

HASH_ITERATIONS = 60000


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, HASH_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, HASH_ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def new_token():
    return secrets.token_urlsafe(32)


def permissions_for(role):
    return PERMISSIONS.get(role, PERMISSIONS["gast"])
