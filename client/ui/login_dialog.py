from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
                               QHBoxLayout, QLabel, QLineEdit, QVBoxLayout)

DEFAULT_SERVER = "http://localhost:8750"


class LoginDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ProjectDash – Anmeldung")
        self.setMinimumWidth(420)
        self.config = config
        layout = QVBoxLayout(self)
        brand = QLabel("❄ ProjectDash")
        brand.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        sub = QLabel("Kältetechnik-Projektcontrolling")
        sub.setObjectName("muted")
        layout.addWidget(brand)
        layout.addWidget(sub)

        form = QFormLayout()
        self.server = QLineEdit(config.get("server", DEFAULT_SERVER))
        self.username = QLineEdit(config.get("last_user", ""))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.remember = QCheckBox("Benutzername merken")
        self.remember.setChecked(bool(self.username.text()))
        form.addRow("Server", self.server)
        form.addRow("Benutzer", self.username)
        form.addRow("Passwort", self.password)
        form.addRow("", self.remember)
        layout.addLayout(form)

        self.error = QLabel("")
        self.error.setStyleSheet("color: #EF4444; font-size: 12px;")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Anmelden")
        buttons.button(QDialogButtonBox.Ok).setObjectName("primary")
        buttons.accepted.connect(self._login)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _login(self):
        from client.api import Api, ApiError

        api = Api(self.server.text())
        try:
            data = api.login(self.username.text().strip(), self.password.text())
        except ApiError as e:
            self.error.setText(str(e))
            return
        self.config["server"] = self.server.text()
        self.config["token"] = data["token"]
        self.config["user"] = data["user"]
        self.config["permissions"] = data["permissions"]
        self.config["last_user"] = self.username.text().strip() if self.remember.isChecked() else ""
        self.accept()
