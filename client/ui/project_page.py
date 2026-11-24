from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QHeaderView,
                               QLabel, QPushButton, QScrollArea, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from client.kpi import ProjectKPI
from client.ui.widgets import Card, GanttWidget, ProgressPair, fmt_eur, fmt_pct


class ProjectPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName("root")
        self.item = None
        self.project = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        head = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title = QLabel("Projekt")
        self.title.setObjectName("h1")
        self.meta = QLabel("")
        self.meta.setObjectName("muted")
        title_box.addWidget(self.title)
        title_box.addWidget(self.meta)
        head.addLayout(title_box)
        head.addStretch(1)
        self.btn_back = QPushButton("← Zurück")
        self.btn_back.clicked.connect(lambda: self.app.goto("dashboard"))
        self.btn_edit = QPushButton("Bearbeiten")
        self.btn_edit.setObjectName("primary")
        self.btn_edit.clicked.connect(self._edit)
        self.btn_pdf = QPushButton("PDF Projektbericht")
        self.btn_pdf.clicked.connect(self._export_pdf)
        for w in (self.btn_back, self.btn_edit, self.btn_pdf):
            head.addWidget(w)
        root.addLayout(head)

        self.cards = QHBoxLayout()
        self.cards.setSpacing(12)
        self.c_prog = Card("Fortschritt (Ist / Soll)", "–")
        self.c_time = Card("Zeitplan", "–")
        self.c_budget = Card("Budget", "–")
        self.c_actual = Card("Ist-Kosten", "–")
        self.c_eac = Card("Prognose Endkosten", "–")
        self.c_hours = Card("Stunden", "–")
        self._add_cards()
        root.addLayout(self.cards)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        inner.setObjectName("root")
        self.inner_layout = QVBoxLayout(inner)
        inner.setLayout(self.inner_layout)
        self.inner_layout.setSpacing(14)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        self.desc = QLabel("")
        self.desc.setWordWrap(True)
        self.inner_layout.addWidget(self.desc)

        self.tabs = QTabWidget()
        self.inner_layout.addWidget(self.tabs)

        gantt_tab = QWidget()
        gantt_layout = QVBoxLayout(gantt_tab)
        self.gantt = GanttWidget([])
        self.gantt_label = QLabel("Blau = Soll-Terminplan, Orange = Ist-Ausführung, rote Linie = heute")
        self.gantt_label.setObjectName("muted")
        gantt_layout.addWidget(self.gantt)
        gantt_layout.addWidget(self.gantt_label)

        self.milestone_table = self._table(["Meilenstein", "Datum Soll", "Datum Ist", "Status", "Gewicht"])
        ms_tab = self._tab(self.milestone_table)
        self.cost_table = self._table(["Kategorie", "Datum", "Beschreibung", "Soll (€)", "Ist (€)"])
        if self.app.can("view_costs"):
            cost_tab = self._tab(self.cost_table)
        self.hours_table = self._table(["Mitarbeiter", "Funktion", "Tätigkeit", "Datum", "Soll (h)", "Ist (h)"])

        self.tabs.addTab(gantt_tab, "Terminplan")
        self.tabs.addTab(self._wrap(self.milestone_table), "Meilensteine")
        if self.app.can("view_costs"):
            self.tabs.addTab(self._wrap(self.cost_table), "Kosten")
        self.tabs.addTab(self._wrap(self.hours_table), "Stunden & Ressourcen")

    def _add_cards(self):
        for c in (self.c_prog, self.c_time, self.c_budget):
            self.cards.addWidget(c)
        if self.app.can("view_costs"):
            for c in (self.c_actual, self.c_eac):
                self.cards.addWidget(c)
        self.cards.addWidget(self.c_hours)

    def _table(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        return t

    def _tab(self, widget):
        pass

    def _wrap(self, table):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(table)
        return w

    def show_project(self, pid):
        self.project = self.app.db.project(pid)
        if not self.project:
            return
        costs = self.app.db.costs(pid) if self.app.can("view_costs") else []
        hours = self.app.db.hours(pid)
        self.item = ProjectKPI(self.project, costs, hours)
        self._refresh()

    def _refresh(self):
        k = self.item
        p = self.project
        self.title.setText(f"{p.get('code')} · {p.get('name')}")
        status_text = self._status_badge_text(p.get("status"))
        self.meta.setText(f"{status_text} | {p.get('location')} | PL: {p.get('manager')} | "
                          f"{p.get('start_plan')} – {p.get('end_plan')}")
        self.desc.setText(p.get("description", ""))
        self.c_prog.set_value(f"{fmt_pct(k.p_act)}", f"Soll: {fmt_pct(k.p_plan)} | SPI {k.spi:.2f}",
                              color="#10B981" if k.p_act >= k.p_plan - 0.03 else "#F59E0B" if k.p_act >= k.p_plan - 0.15 else "#EF4444")
        self.c_time.set_value(f"{k.date_variance:+d} Tage" if k.date_variance else "im Plan",
                              f"Ende Prognose: {k.forecast.isoformat()}",
                              color="#EF4444" if k.date_variance > 0 else "#10B981")
        self.c_budget.set_value(fmt_eur(k.budget, compact=True))
        if self.app.can("view_costs"):
            delta = k.cost_actual - k.pv
            self.c_actual.set_value(fmt_eur(k.cost_actual, compact=True),
                                    ("+" if delta > 0 else "") + fmt_eur(delta, compact=True) + " ggü. Plan bis heute",
                                    color="#EF4444" if delta > 0 else "#10B981")
            vac = k.vac
            self.c_eac.set_value(fmt_eur(k.eac, compact=True),
                                 ("+" if vac < 0 else "") + fmt_eur(abs(vac), compact=True) + " ggü. Budget | CPI " + f"{k.cpi:.2f}",
                                 color="#EF4444" if vac < 0 else "#10B981")
        self.c_hours.set_value(f"{k.hours_actual:,.0f} h".replace(",", "."),
                               f"Soll: {k.hours_plan:,.0f} h".replace(",", "."))

        phases = self.app.db.phases(self.project["id"])
        self.gantt.phases = phases
        self.gantt.start = p.get("start_plan")
        self.gantt.end = p.get("end_plan")
        from datetime import datetime

        lo, hi = self.gantt._range()
        self.gantt.setMinimumHeight(max(len(phases) * 34 + 40, 140))
        self.gantt.update()

        self._fill_table(self.milestone_table, self._milestone_rows(self.app.db.milestones(self.project["id"])))
        if self.app.can("view_costs"):
            self._fill_table(self.cost_table, self._cost_rows(self.app.db.costs(self.project["id"])))
        self._fill_table(self.hours_table, self._hours_rows(self.app.db.hours(self.project["id"])))
        self.btn_edit.setVisible(self.app.can("edit_projects"))
        self.btn_pdf.setVisible(self.app.can("export_pdf"))

    def _status_badge_text(self, status):
        return {"laufend": "🟢 Laufend", "kritisch": "🔴 Kritisch",
                "geplant": "🔵 Geplant", "abgeschlossen": "✅ Abgeschlossen"}.get(status, status)

    def _milestone_rows(self, rows):
        out = []
        for m in rows:
            out.append([m.get("name", ""), str(m.get("date_plan") or "")[:10],
                        str(m.get("date_actual") or "–")[:10],
                        "erreicht" if m.get("date_actual") else "offen",
                        f"{(m.get('weight') or 0)*100:.0f} %"])
        return out

    def _cost_rows(self, rows):
        return [[c.get("category", ""), str(c.get("date") or "")[:10], c.get("description", ""),
                 f"{(c.get('amount_plan') or 0):,.0f}".replace(",", "."), f"{(c.get('amount_actual') or 0):,.0f}".replace(",", ".")]
                for c in rows]

    def _hours_rows(self, rows):
        return [[h.get("employee", ""), h.get("role", ""), h.get("task", ""),
                 str(h.get("date") or "")[:10],
                 f"{(h.get('hours_plan') or 0):,.0f}".replace(",", "."),
                 f"{(h.get('hours_actual') or 0):,.0f}".replace(",", ".")]
                for h in rows]

    def _fill_table(self, table, rows):
        table.setRowCount(0)
        for r in rows:
            table.insertRow(table.rowCount())
            for col, val in enumerate(r):
                table.setItem(table.rowCount() - 1, col, QTableWidgetItem(str(val)))

    def _edit(self):
        if not self.app.can("edit_projects"):
            return
        from client.ui.project_edit_dialog import ProjectEditDialog

        dlg = ProjectEditDialog(self.app, self.project, self)
        if dlg.exec() and dlg.result_data:
            self.app.push_rows("projects", [dlg.result_data])
            self.project = self.app.db.project(self.project["id"])
            self.item = ProjectKPI(self.project, self.app.db.costs(self.project["id"]) if self.app.can("view_costs") else [],
                                   self.app.db.hours(self.project["id"]))
            self._refresh()

    def _export_pdf(self):
        from client import pdf_report

        default = f"projektbericht_{self.project.get('code')}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "PDF speichern", default, "PDF (*.pdf)")
        if not path:
            return
        pid = self.project["id"]
        pdf_report.project_report(path, self.item, self.app.db.phases(pid),
                                  self.app.db.milestones(pid), self.app.db.costs(pid), self.app.db.hours(pid))
        self.app.status(f"PDF gespeichert: {path}")
