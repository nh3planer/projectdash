from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFormLayout, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from server.auth import PERMISSIONS, ROLES

PERM_LABELS = {
    "view_projects": "Projekte sehen",
    "edit_projects": "Projekte bearbeiten",
    "view_costs": "Kosten sehen",
    "edit_costs": "Kosten bearbeiten",
    "view_hours": "Stunden sehen",
    "edit_hours": "Stunden erfassen",
    "view_management": "Management-KPIs sehen",
    "manage_users": "Benutzer verwalten",
    "import_data": "Daten importieren",
    "export_data": "Daten exportieren",
    "export_pdf": "PDF-Reports erstellen",
}

ROLE_LABELS = {
    "admin": "Administrator (alle Rechte, Benutzerverwaltung)",
    "management": "Management (inkl. Management-KPIs, vertraulich)",
    "projektleiter": "Projektleitung (Projekte, Kosten, Stunden, Import/Export)",
    "mitarbeiter": "Mitarbeiter (Stunden erfassen, Projekte lesend)",
    "gast": "Gast (nur Projektliste, keine Kosten)",
}


class UserEditDialog(QDialog):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Benutzer anlegen" if user is None else "Benutzer bearbeiten")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.username = QLineEdit(user["username"] if user else "")
        self.username.setEnabled(user is None)
        self.full_name = QLineEdit(user["full_name"] if user else "")
        self.email = QLineEdit(user["email"] if user else "")
        self.role = QComboBox()
        for r in ROLES:
            self.role.addItem(ROLE_LABELS[r], r)
        if user:
            self.role.setCurrentIndex(ROLES.index(user["role"]))
        else:
            self.role.setCurrentIndex(ROLES.index("mitarbeiter"))
        self.active = QCheckBox("Aktiv")
        self.active.setChecked(user["active"] if user else True)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        pw_hint = QLabel("leer lassen = unverändert")
        pw_hint.setObjectName("muted")
        pw_box = QHBoxLayout()
        pw_box.addWidget(self.password)
        pw_box.addWidget(pw_hint)
        form.addRow("Benutzername", self.username)
        form.addRow("Name", self.full_name)
        form.addRow("E-Mail", self.email)
        form.addRow("Rolle", self.role)
        form.addRow("Passwort", pw_box)
        form.addRow("", self.active)
        layout.addLayout(form)

        perm_box = QVBoxLayout()
        perm_box.addWidget(QLabel("Rechte dieser Rolle:"))
        for perm in PERMISSIONS["admin"]:
            cb = QCheckBox(PERM_LABELS.get(perm, perm))
            cb.setEnabled(False)
            cb.setObjectName(perm)
            perm_box.addWidget(cb)
        layout.addLayout(perm_box)
        self.role.currentIndexChanged.connect(self._refresh_perms)
        self._refresh_perms()

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_perms(self):
        role = self.role.currentData()
        perms = set(PERMISSIONS.get(role, []))
        for cb in self.findChildren(QCheckBox):
            if not cb.isEnabled():
                cb.setChecked(cb.objectName() in perms)

    def payload(self):
        return {
            "username": self.username.text().strip(),
            "full_name": self.full_name.text().strip(),
            "email": self.email.text().strip(),
            "role": self.role.currentData(),
            "active": self.active.isChecked(),
            "password": self.password.text(),
        }

    def _save(self):
        if not self.username.text().strip() or not self.full_name.text().strip():
            QMessageBox.warning(self, "Pflichtfelder", "Benutzername und Name sind Pflichtfelder.")
            return
        if self.user is None and len(self.password.text()) < 6:
            QMessageBox.warning(self, "Passwort", "Initialpasswort muss mindestens 6 Zeichen haben.")
            return
        self.accept()


class UsersPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName("root")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)
        head = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Benutzer & Rechte")
        title.setObjectName("h1")
        title_box.addWidget(title)
        title_box.addWidget(QLabel("Rollen verwalten, Rechte einstellen, Passwörter zurücksetzen", objectName="muted"))
        head.addLayout(title_box)
        head.addStretch(1)
        btn_add = QPushButton("Neuer Benutzer")
        btn_add.setObjectName("success")
        btn_add.clicked.connect(self._add)
        self.btn_add = btn_add
        head.addWidget(btn_add)
        root.addLayout(head)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Benutzername", "Name", "E-Mail", "Rolle", "Status", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(5, 90)
        root.addWidget(self.table)

        self.table.cellClicked.connect(self._on_click)
        self._edit_buttons = {}

    def refresh(self):
        self.users = {}
        try:
            self.users_list = self.app.api.users()
        except Exception as e:
            self.users_list = self.app.db.users()
            self.app.status(f"Offline-Modus: Benutzertabelle aus Cache ({e})")
        self.table.setRowCount(0)
        for u in self.users_list:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(u.get("username", "")))
            self.table.setItem(row, 1, QTableWidgetItem(u.get("full_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(u.get("email", "")))
            role_item = QTableWidgetItem(ROLE_LABELS.get(u.get("role"), u.get("role", "")))
            role_item.setToolTip(", ".join(PERM_LABELS.get(p, p) for p in PERMISSIONS.get(u.get("role"), [])))
            self.table.setItem(row, 3, role_item)
            self.table.setItem(row, 4, QTableWidgetItem("✔ aktiv" if u.get("active") else "✖ gesperrt"))
            btn = QPushButton("Bearbeiten")
            self._edit_buttons[row] = (btn, u)
            btn.clicked.connect(lambda _, r=row: self._edit(r))
            self.table.setCellWidget(row, 5, btn)
            self.users[row] = u

    def _on_click(self, row, col):
        pass

    def _add(self):
        dlg = UserEditDialog(self)
        if dlg.exec():
            try:
                self.app.api.create_user(dlg.payload())
                self.app.status(f"Benutzer {dlg.payload()['username']} angelegt")
            except Exception as e:
                QMessageBox.warning(self, "Fehler", str(e))
            self.refresh()
            self.app.sync()

    def _edit(self, row):
        u = self.users.get(row)
        if not u:
            return
        dlg = UserEditDialog(self, dict(u))
        if dlg.exec():
            payload = dlg.payload()
            try:
                self.app.api.update_user(u["id"], payload)
                self.app.status(f"Benutzer {payload['username']} aktualisiert")
            except Exception as e:
                QMessageBox.warning(self, "Fehler", str(e))
            self.refresh()
            self.app.sync()
