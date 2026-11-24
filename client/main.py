import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "client") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "client"))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QScrollArea,
                               QStackedWidget, QVBoxLayout, QWidget)

from client import excel_io
from client import pdf_report as pdf_mod
from client.api import Api, ApiError
from client.kpi import PortfolioKPI
from client.localdb import LocalDB
from client.ui.dashboard_page import DashboardPage
from client.ui.data_page import DataPage
from client.ui.login_dialog import DEFAULT_SERVER, LoginDialog
from client.ui.management_page import ManagementPage
from client.ui.project_page import ProjectPage
from client.ui.users_page import UsersPage
from client.theme import QSS

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".projectdash", "client.json")


def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


class App:
    def __init__(self, db, api, user, permissions):
        self.db = db
        self.api = api
        self.user = user
        self.permissions = permissions
        self.sync_date = "–"
        self.window = None

    def can(self, perm):
        return perm in self.permissions

    def status(self, text):
        if self.window:
            self.window.statusBar().showMessage(text, 8000)

    def sync(self):
        since = self.db.get_meta("last_sync", "")
        payload = self.api.sync(since)
        self.db.full_sync(payload)
        self.sync_date = payload["server_time"].replace("T", " ")[:16]
        return payload

    def push_rows(self, table, rows):
        try:
            result = self.api.push(table, rows)
        except ApiError as e:
            if self.can("edit_projects") or self.can("edit_hours") or self.can("edit_costs"):
                self.db.apply(table, rows)
            self.status(f"Offline gespeichert, Sync später: {e}")
            return [r.get("id") for r in rows]
        new_ids = result.get("accepted_ids", [])
        for row, rid in zip(rows, new_ids):
            if not row.get("id"):
                row["id"] = rid
        self.db.apply(table, rows)
        return new_ids

    def refresh_all(self):
        if self.window:
            self.window.refresh_all()

    def open_project(self, pid):
        if self.window:
            self.window.show_project(pid)

    def goto(self, page):
        if self.window:
            self.window.goto(page)

    def export_excel(self):
        from client import excel_io

        path, _ = QFileDialog.getSaveFileName(None, "Excel-Export speichern",
                                              "projectdash_export.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        portfolio = self._portfolio()
        sheets = [("Projekte", excel_io.PROJECT_FIELDS_EXPORT,
                   self._project_rows_for_export())]
        by_code = {p["code"]: p["id"] for p in self.db.projects()}
        ms_rows, cost_rows, hours_rows = [], [], []
        code_by_pid = {p["id"]: p["code"] for p in self.db.projects()}
        for m in self.db.rows("milestones"):
            ms_rows.append({"project_code": code_by_pid.get(m["project_id"]), "name": m["name"],
                            "date_plan": m["date_plan"], "date_actual": m["date_actual"],
                            "weight": m["weight"]})
        sheets.append(("Meilensteine", excel_io.MILESTONE_FIELDS, ms_rows))
        if self.can("view_costs"):
            for c in self.db.rows("cost_entries"):
                cost_rows.append({"project_code": code_by_pid.get(c["project_id"]), "date": c["date"],
                                  "category": c["category"], "description": c["description"],
                                  "amount_plan": c["amount_plan"], "amount_actual": c["amount_actual"]})
            sheets.append(("Kosten", excel_io.COST_FIELDS, cost_rows))
        for h in self.db.rows("hours_entries"):
            hours_rows.append({"project_code": code_by_pid.get(h["project_id"]), "date": h["date"],
                               "employee": h["employee"], "role": h["role"], "task": h["task"],
                               "hours_plan": h["hours_plan"], "hours_actual": h["hours_actual"]})
        sheets.append(("Stunden", excel_io.HOURS_FIELDS, hours_rows))
        excel_io.export_workbook(sheets).save(path)
        self.status(f"Excel exportiert: {path}")

    def _project_rows_for_export(self):
        rows = []
        for p in self.db.projects():
            row = {k: p.get(k) for k, _t, _w in excel_io.PROJECT_FIELDS_EXPORT}
            rows.append(row)
        return rows

    def _portfolio(self):
        projects = self.db.projects()
        costs_by_pid, hours_by_pid = {}, {}
        if self.can("view_costs"):
            for c in self.db.rows("cost_entries"):
                costs_by_pid.setdefault(c["project_id"], []).append(c)
        for h in self.db.rows("hours_entries"):
            hours_by_pid.setdefault(h["project_id"], []).append(h)
        return PortfolioKPI(projects, costs_by_pid, hours_by_pid)

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(None, "Portfolio-Report speichern",
                                              "projectdash_portfolio.pdf", "PDF (*.pdf)")
        if not path:
            return
        pdf_mod.portfolio_report(path, self._portfolio())
        self.status(f"PDF gespeichert: {path}")


class MainWindow(QMainWindow):
    NAV = [
        ("dashboard", "📊  Projektübersicht", "view_projects"),
        ("project", "🧊  Projekt-Detail", "view_projects"),
        ("management", "🔒  Management-Cockpit", "view_management"),
        ("data", "📁  Daten-Import/Export", "export_data"),
        ("users", "👥  Benutzer & Rechte", "manage_users"),
    ]

    def __init__(self, app):
        super().__init__()
        self.app = app
        app.window = self
        self.setWindowTitle("ProjectDash – Kältetechnik Projektcontrolling")
        self.resize(1440, 900)
        central = QWidget()
        central.setObjectName("root")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setStyleSheet("QWidget { background-color: #111C33; }")
        sidebar.setFixedWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 16, 12, 16)
        brand = QLabel("❄ ProjectDash")
        brand.setObjectName("brand")
        side_layout.addWidget(brand)
        self.nav_buttons = {}
        for key, label, perm in self.NAV:
            if not app.can(perm):
                continue
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, k=key: self.goto(k))
            self.nav_buttons[k] = btn
            side_layout.addWidget(btn)
        side_layout.addStretch(1)
        user_box = QVBoxLayout()
        self.user_label = QLabel("👤 " + (app.user.get("full_name") or app.user.get("username", "")))
        self.user_label.setObjectName("muted")
        self.user_label.setWordWrap(True)
        role_label = QLabel(app.user.get("role", "").capitalize())
        role_label.setObjectName("kpiTitle")
        btn_sync = QPushButton("🔄 Jetzt synchronisieren")
        btn_sync.setObjectName("ghost")
        btn_sync.clicked.connect(self.force_sync)
        btn_pw = QPushButton("Passwort ändern")
        btn_pw.setObjectName("ghost")
        btn_pw.clicked.connect(self.change_password)
        btn_logout = QPushButton("Abmelden")
        btn_logout.setObjectName("ghost")
        btn_logout.clicked.connect(self.logout)
        for w in (self.user_label, role_label, btn_sync, btn_pw, btn_logout):
            user_box.addWidget(w)
        side_layout.addLayout(user_box)
        layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("root")
        layout.addWidget(self.stack, 1)

        self.pages = {}
        self.pages["dashboard"] = DashboardPage(app)
        self.stack.addWidget(self.pages["dashboard"])
        self.pages["project"] = ProjectPage(app)
        self.stack.addWidget(self.pages["project"])
        if app.can("view_management"):
            self.pages["management"] = ManagementPage(app)
            self.stack.addWidget(self.pages["management"])
        if app.can("export_data"):
            self.pages["data"] = DataPage(app)
            self.stack.addWidget(self.pages["data"])
        if app.can("manage_users"):
            self.pages["users"] = UsersPage(app)
            self.stack.addWidget(self.pages["users"])

        self.setCentralWidget(central)
        self.statusBar().showMessage("Bereit")
        self.sync_label = QLabel()
        self.statusBar().addPermanentWidget(self.sync_label)

    def goto(self, key):
        if key not in self.pages:
            return
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        self.stack.setCurrentWidget(self.pages[key])
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh()

    def refresh_all(self):
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    pass
        self.sync_label.setText(f"Letzter Sync: {self.app.sync_date}")

    def force_sync(self):
        try:
            self.app.sync()
            self.refresh_all()
            self.status("Synchronisation abgeschlossen")
        except ApiError as e:
            self.status(f"Sync nicht möglich: {e}")

    def show_project(self, pid):
        self.goto("project")
        self.pages["project"].show_project(pid)

    def change_password(self):
        from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout,
                                       QLabel, QLineEdit, QMessageBox, QVBoxLayout)

        dlg = QDialog(self)
        dlg.setWindowTitle("Passwort ändern")
        form = QFormLayout(dlg)
        old = QLineEdit()
        old.setEchoMode(QLineEdit.Password)
        new = QLineEdit()
        new.setEchoMode(QLineEdit.Password)
        err = QLabel("")
        err.setStyleSheet("color:#EF4444")
        form.addRow("Alt", old)
        form.addRow("Neu", new)
        form.addRow(err)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        if dlg.exec():
            try:
                self.app.api.change_password(old.text(), new.text())
                QMessageBox.information(self, "Erfolg", "Passwort geändert.")
            except ApiError as e:
                QMessageBox.warning(self, "Fehler", str(e))

    def logout(self):
        cfg = load_config()
        cfg.pop("token", None)
        save_config(cfg)
        self.status("Abgemeldet – bitte die Anwendung neu starten")
        self.close()


def start():
    cfg = load_config()
    token = cfg.get("token")
    server = cfg.get("server", DEFAULT_SERVER)
    api = Api(server, token)
    user, permissions = cfg.get("user"), cfg.get("permissions", [])
    if token:
        try:
            result = api.verify()
            user, permissions = result["user"], result["permissions"]
        except Exception:
            dlg = LoginDialog(cfg)
            if dlg.exec():
                token = cfg.get("token")
                api = Api(cfg.get("server"), token)
                user, permissions = cfg["user"], cfg["permissions"]
            else:
                return
    else:
        dlg = LoginDialog(cfg)
        if dlg.exec():
            token = cfg.get("token")
            api = Api(cfg.get("server"), token)
            user, permissions = cfg["user"], cfg["permissions"]
        else:
            return
    save_config({**cfg, "token": token, "user": user, "permissions": permissions})
    db = LocalDB()
    app_ctrl = App(db, api, user, permissions)
    try:
        app_ctrl.sync()
    except ApiError as e:
        pass
    win = MainWindow(app_ctrl)
    win.refresh_all()
    win.goto("dashboard")
    win.show()
    return win


def main():
    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setStyleSheet(QSS)
    win = start()
    if win:
        sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
