from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
                               QTextEdit, QVBoxLayout, QDateEdit)

from client.theme import SIZE_LABELS

STATUSES = ["geplant", "laufend", "kritisch", "abgeschlossen"]
PRIORITIES = ["niedrig", "normal", "hoch"]


class ProjectEditDialog(QDialog):
    def __init__(self, app, project, parent=None):
        super().__init__(parent)
        self.app = app
        self.project = project
        self.result_data = None
        self.setWindowTitle("Projekt bearbeiten" if project else "Neues Projekt")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.code = QLineEdit(project.get("code") if project else "")
        self.name = QLineEdit(project.get("name") if project else "")
        self.description = QTextEdit(project.get("description") if project else "")
        self.description.setFixedHeight(70)
        self.size = QComboBox()
        for key, label in SIZE_LABELS.items():
            self.size.addItem(label, key)
        if project:
            self.size.setCurrentIndex(max(0, list(SIZE_LABELS).index(project.get("size_class", "mittel"))))
        self.status = QComboBox()
        self.status.addItems(STATUSES)
        if project:
            self.status.setCurrentText(project.get("status", "laufend"))
        self.priority = QComboBox()
        self.priority.addItems(PRIORITIES)
        if project:
            self.priority.setCurrentText(project.get("priority", "normal"))
        self.location = QLineEdit(project.get("location") if project else "")
        self.manager = QLineEdit(project.get("manager") if project else "")

        self.start = QDateEdit()
        self._set_date(self.start, project, "start_plan")
        self.end = QDateEdit()
        self._set_date(self.end, project, "end_plan")
        self.forecast = QDateEdit()
        self._set_date(self.forecast, project, "end_forecast")

        self.budget = QDoubleSpinBox()
        self.budget.setRange(0, 100_000_000)
        self.budget.setSuffix(" €")
        self.budget.setValue(project.get("budget", 0) if project else 0)
        self.p_plan = QSpinBox()
        self.p_plan.setRange(0, 100)
        self.p_plan.setSuffix(" %")
        self.p_plan.setValue(int((project.get("progress_plan") or 0) * 100) if project else 0)
        self.p_act = QSpinBox()
        self.p_act.setRange(0, 100)
        self.p_act.setSuffix(" %")
        self.p_act.setValue(int((project.get("progress_actual") or 0) * 100) if project else 0)

        form.addRow("Code", self.code)
        form.addRow("Name", self.name)
        form.addRow("Beschreibung", self.description)
        form.addRow("Größe", self.size)
        form.addRow("Status", self.status)
        form.addRow("Priorität", self.priority)
        form.addRow("Ort", self.location)
        form.addRow("Projektleitung", self.manager)
        form.addRow("Start (Soll)", self.start)
        form.addRow("Ende (Soll)", self.end)
        form.addRow("Ende (Prognose)", self.forecast)
        form.addRow("Budget", self.budget)
        form.addRow("Fortschritt Soll", self.p_plan)
        form.addRow("Fortschritt Ist", self.p_act)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_date(self, widget, project, key):
        from PySide6.QtCore import QDate

        widget.setCalendarPopup(True)
        val = (project or {}).get(key)
        if val:
            d = QDate.fromString(str(val)[:10], "yyyy-MM-dd")
            widget.setDate(d)
        else:
            widget.setDate(QDate.currentDate())

    def _save(self):
        if not self.code.text().strip() or not self.name.text().strip():
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Pflichtfelder", "Code und Name sind Pflichtfelder.")
            return
        self.result_data = {
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "description": self.description.toPlainText(),
            "size_class": self.size.currentData(),
            "status": self.status.currentText(),
            "priority": self.priority.currentText(),
            "location": self.location.text().strip(),
            "manager": self.manager.text().strip(),
            "start_plan": self.start.date().toString("yyyy-MM-dd"),
            "end_plan": self.end.date().toString("yyyy-MM-dd"),
            "end_forecast": self.forecast.date().toString("yyyy-MM-dd"),
            "budget": self.budget.value(),
            "progress_plan": self.p_plan.value() / 100,
            "progress_actual": self.p_act.value() / 100,
        }
        if self.project:
            self.result_data["id"] = self.project["id"]
        self.accept()
