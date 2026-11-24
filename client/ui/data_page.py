from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from client import excel_io
from client.kpi import PortfolioKPI
from client.ui.widgets import fmt_eur


class DataPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName("root")
        self.pending = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.addWidget(QLabel("Daten-Import & -Export", objectName="h1"))
        title_box.addWidget(QLabel("Excel-Import aktualisiert Projekte über den Projekt-Code; "
                                   "Meilensteine/Kosten/Stunden werden über den Projekt-Code zugeordnet.",
                                  objectName="muted"))
        root.addLayout(title_box)

        actions = QHBoxLayout()
        btn_import = QPushButton("Excel-Import…")
        btn_import.setObjectName("primary")
        btn_import.clicked.connect(self._import)
        btn_template = QPushButton("Import-Vorlage herunterladen")
        btn_template.clicked.connect(self._template)
        btn_export = QPushButton("Alles als Excel exportieren")
        btn_export.setObjectName("success")
        btn_export.clicked.connect(lambda: self.app.export_excel())
        actions.addWidget(btn_import)
        actions.addWidget(btn_template)
        actions.addWidget(btn_export)
        actions.addStretch(1)
        root.addLayout(actions)

        root.addWidget(QLabel("Vorschau der zu importierenden Daten:", objectName="h2"))
        self.preview = QTableWidget(0, 4)
        self.preview.setHorizontalHeaderLabels(["Tabelle", "Zeilen", "Neu", "Aktualisiert"])
        self.preview.verticalHeader().setVisible(False)
        root.addWidget(self.preview)

        buttons = QHBoxLayout()
        btn_apply = QPushButton("Import anwenden")
        btn_apply.setObjectName("success")
        btn_apply.clicked.connect(self._apply)
        self.btn_apply = btn_apply
        btn_cancel = QPushButton("Verwerfen")
        btn_cancel.clicked.connect(self._clear)
        self.btn_cancel = btn_cancel
        buttons.addWidget(btn_apply)
        buttons.addWidget(btn_cancel)
        buttons.addStretch(1)
        root.addLayout(buttons)
        root.addStretch(1)

    def refresh(self):
        self.btn_apply.setVisible(bool(self.pending))
        self.btn_cancel.setVisible(bool(self.pending))

    def _template(self):
        path, _ = QFileDialog.getSaveFileName(self, "Vorlage speichern", "projectdash_import_vorlage.xlsx",
                                              "Excel (*.xlsx)")
        if not path:
            return
        sheets = [
            ("Projekte", excel_io.PROJECT_FIELDS, [{"code": "K-2001", "name": "Beispielprojekt",
                                                    "description": "", "size_class": "klein",
                                                    "status": "geplant", "priority": "normal",
                                                    "location": "", "manager": "",
                                                    "start_plan": "2026-01-01", "end_plan": "2026-06-30",
                                                    "end_forecast": "", "budget": 50000,
                                                    "progress_plan": 0, "progress_actual": 0}]),
            ("Meilensteine", excel_io.MILESTONE_FIELDS,
             [{"project_code": "K-2001", "name": "Abnahme", "date_plan": "2026-06-30",
               "date_actual": "", "weight": 1.0}]),
            ("Kosten", excel_io.COST_FIELDS,
             [{"project_code": "K-2001", "date": "2026-02-01", "category": "Material",
               "description": "", "amount_plan": 20000, "amount_actual": 0}]),
            ("Stunden", excel_io.HOURS_FIELDS,
             [{"project_code": "K-2001", "date": "2026-02-01", "employee": "Max Muster",
               "role": "Montage", "task": "Rohrleitungsbau", "hours_plan": 40, "hours_actual": 0}]),
        ]
        excel_io.export_workbook(sheets).save(path)
        self.app.status(f"Vorlage gespeichert: {path}")

    def _import(self):
        if not self.app.can("import_data") and not self.app.can("edit_costs"):
            self.app.status("Keine Importrechte")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Excel-Datei wählen", "", "Excel (*.xlsx *.xlsm)")
        if not path:
            return
        try:
            self.pending = excel_io.import_workbook(path)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Importfehler", f"Datei konnte nicht gelesen werden:\n{e}")
            return
        self._preview()
        self.refresh()
        self.app.status(f"Import bereit: {path}")

    def _preview(self):
        self.preview.setRowCount(0)
        for table, rows in self.pending.items():
            self.preview.insertRow(self.preview.rowCount())
            self.preview.setItem(self.preview.rowCount() - 1, 0, QTableWidgetItem(table))
            self.preview.setItem(self.preview.rowCount() - 1, 1, QTableWidgetItem(str(len(rows))))

    def _apply(self):
        from client.localdb import EDITABLE

        pushed = 0
        by_code = {p["code"]: p["id"] for p in self.app.db.projects()}
        for table, rows in self.pending.items():
            clean_rows = []
            for row in rows:
                row = {k: v for k, v in row.items() if k in EDITABLE.get(table, set()) or k == "project_code"}
                code = row.pop("project_code", None)
                if table != "projects":
                    pid = by_code.get(code) if code else None
                    if not pid:
                        continue
                    row["project_id"] = pid
                else:
                    if not row.get("code"):
                        continue
                    if row["code"] in by_code:
                        row["id"] = by_code[row["code"]]
                for key, val in list(row.items()):
                    if val is None:
                        row[key] = ""
                clean_rows.append(row)
            if clean_rows:
                self.app.push_rows(table, clean_rows)
                pushed += len(clean_rows)
        self.app.status(f"Import abgeschlossen: {pushed} Datensätze synchronisiert")
        self._clear()
        self.app.refresh_all()

    def _clear(self):
        self.pending = {}
        self.preview.setRowCount(0)
        self.refresh()
