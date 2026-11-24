from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from client import kpi as kpi_mod
from client.kpi import PortfolioKPI
from client.ui import widgets
from client.ui.widgets import Card, ProjectTable, fmt_eur


class DashboardPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName("root")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title = QLabel("Projektübersicht")
        self.title.setObjectName("h1")
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("muted")
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box)
        header.addStretch(1)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Alle Status", "Geplant", "Laufend", "Kritisch", "Abgeschlossen"])
        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.size_filter = QComboBox()
        self.size_filter.addItems(["Alle Größen", "Kleinprojekte", "Mittelprojekte", "Großprojekte"])
        self.size_filter.currentIndexChanged.connect(self.refresh)

        self.btn_new = QPushButton("Neues Projekt")
        self.btn_new.setObjectName("success")
        self.btn_new.clicked.connect(self._new_project)
        self.btn_export = QPushButton("Excel Export")
        self.btn_export.clicked.connect(lambda: self._request("export_excel"))
        self.btn_pdf = QPushButton("PDF Report")
        self.btn_pdf.clicked.connect(lambda: self._request("export_pdf"))
        for w in (self.status_filter, self.size_filter, self.btn_export, self.btn_pdf, self.btn_new):
            header.addWidget(w)
        root.addLayout(header)

        self.cards = QHBoxLayout()
        self.cards.setSpacing(12)
        self.card_projects = self._card("Projekte", "–", "– Projekte laufend")
        self.card_budget = self._card("Gesamtbudget", "–", "")
        self.card_actual = self._card("Ist-Kosten", "–", "ggü. Plan bis heute")
        self.card_forecast = self._card("Prognose Endkosten", "–", "ggü. Budget")
        self.card_terms = self._card("Terminlage", "–", "im Plan")
        root.addLayout(self.cards)

        self.table = ProjectTable(show_costs=self.app.can("view_costs"))
        self.table.open_requested = self._open_project
        root.addWidget(self.table, 3)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        self.chart_costs = self._chart_panel("Budget vs. Ist-Kosten (T€)")
        self.chart_status = self._chart_panel("Projekte nach Status")
        charts_row.addWidget(self.chart_costs, 3)
        charts_row.addWidget(self.chart_status, 2)
        root.addLayout(charts_row, 2)

    def _card(self, title, value, sub=""):
        c = Card(title, value, sub)
        self.cards.addWidget(c)
        return c

    def _chart_panel(self, title):
        from PySide6.QtCharts import QBarSeries, QBarSet, QCategoryAxis, QChart, QChartView, QPieSeries, QValueAxis
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setObjectName("h2")
        layout.addWidget(label)
        chart = QChart()
        chart.setBackgroundVisible(False)
        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background: transparent;")
        layout.addWidget(view)
        panel._chart = chart
        return panel

    def _request(self, action):
        if hasattr(self.app, action):
            getattr(self.app, action)()

    def _new_project(self):
        if not self.app.can("edit_projects"):
            return
        from client.ui.project_edit_dialog import ProjectEditDialog

        dlg = ProjectEditDialog(self.app, None, self)
        if dlg.exec() and dlg.result_data:
            self.app.push_rows("projects", [dlg.result_data])
            self.refresh()

    def _open_project(self, pid):
        self.app.open_project(pid)

    def refresh(self):
        if not self.app.db.has_data():
            return
        projects = self.app.db.projects()
        costs_by_pid, hours_by_pid = {}, {}
        if self.app.can("view_costs"):
            for c in self.app.db.rows("cost_entries"):
                costs_by_pid.setdefault(c["project_id"], []).append(c)
        for h in self.app.db.rows("hours_entries"):
            hours_by_pid.setdefault(h["project_id"], []).append(h)

        size_map = {"Kleinprojekte": "klein", "Mittelprojekte": "mittel", "Großprojekte": "gross"}
        status_map = {"Geplant": "geplant", "Laufend": "laufend", "Kritisch": "kritisch",
                      "Abgeschlossen": "abgeschlossen"}
        projects = [p for p in projects
                    if self.size_filter.currentIndex() == 0
                    or p.get("size_class") == size_map[self.size_filter.currentText()]]
        projects = [p for p in projects
                    if self.status_filter.currentIndex() == 0
                    or p.get("status") == status_map[self.status_filter.currentText()]]
        portfolio = PortfolioKPI(projects, costs_by_pid, hours_by_pid)
        self.portfolio = portfolio
        self.subtitle.setText(f"Soll-/Ist-Vergleich aller Projekte, Stand {self.app.sync_date}")
        self.card_projects.set_value(str(portfolio.count), f"{portfolio.running} laufend · {portfolio.critical} kritisch · {portfolio.done} abgeschlossen")
        self.card_budget.set_value(fmt_eur(portfolio.total_budget, compact=True))
        delta = portfolio.total_actual - portfolio.total_plan_now
        self.card_actual.set_value(fmt_eur(portfolio.total_actual, compact=True),
                                    ("+" if delta > 0 else "") + fmt_eur(delta, compact=True) + " ggü. Plan bis heute",
                                    color="#EF4444" if delta > 0 else "#10B981")
        fd = portfolio.forecast_delta
        self.card_forecast.set_value(fmt_eur(portfolio.total_forecast, compact=True),
                                     ("+" if fd > 0 else "") + fmt_eur(fd, compact=True) + " ggü. Budget",
                                     color="#EF4444" if fd > 0 else "#10B981")
        late = [i for i in portfolio.items if i.date_variance > 0 and i.project.get("status") != "abgeschlossen"]
        self.card_terms.set_value(f"{len(late)} kritisch" if late else "Alles im Plan",
                                  f"{len(portfolio.on_time)} Projekte termintreu", color="#EF4444" if late else "#10B981")
        self.table.fill(sorted(portfolio.items, key=lambda i: i.project.get("code", "")))
        self.btn_new.setVisible(self.app.can("edit_projects"))
        self.btn_export.setVisible(self.app.can("export_data"))
        self.btn_pdf.setVisible(self.app.can("export_pdf"))
        self._draw_charts(portfolio)

    def _draw_charts(self, portfolio):
        from PySide6.QtCharts import QBarSeries, QBarSet, QCategoryAxis, QPieSeries, QValueAxis
        import client.theme as theme

        chart = self.chart_costs._chart
        chart.removeAllSeries()
        for axis in chart.axes():
            chart.removeAxis(axis)
        series = QBarSeries()
        budget_set = QBarSet("Budget (T€)")
        actual_set = QBarSet("Ist (T€)")
        cats = QCategoryAxis()
        items = sorted(portfolio.items, key=lambda i: i.project.get("code", ""))
        for idx, i in enumerate(items):
            budget_set.append(round(i.budget / 1000, 1))
            actual_set.append(round(i.cost_actual / 1000, 1))
            cats.append(i.project.get("code", ""), idx)
        series.append(budget_set)
        series.append(actual_set)
        budget_set.setColor(QColor("#2563EB"))
        actual_set.setColor(QColor("#F59E0B"))
        chart.addSeries(series)
        chart.createDefaultAxes()
        axis_x = chart.axes()[0]
        for axis in list(chart.axes()):
            chart.removeAxis(axis)
        chart.addAxis(cats, Qt.AlignBottom)
        chart.addAxis(QValueAxis(), Qt.AlignLeft)
        series.attachAxis(cats)
        series.attachAxis(chart.axes()[-1])
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor("#94A3B8"))
        chart.setTitle("")

        pie_chart = self.chart_status._chart
        pie_chart.removeAllSeries()
        for axis in pie_chart.axes():
            pie_chart.removeAxis(axis)
        pie = QPieSeries()
        color_map = {"geplant": "#3B82F6", "laufend": "#10B981", "kritisch": "#EF4444",
                     "abgeschlossen": "#6B7280"}
        counts = {}
        for i in portfolio.items:
            counts[i.project.get("status", "?")] = counts.get(i.project.get("status", "?"), 0) + 1
        for status, count in counts.items():
            slice_ = pie.append(f"{status.capitalize()} ({count})", count)
            slice_.setBrush(QColor(color_map.get(status, "#64748B")))
            slice_.setLabelColor(QColor("#CBD5E1"))
        pie_chart.addSeries(pie)
        pie_chart.legend().setVisible(True)
        pie_chart.legend().setLabelColor(QColor("#94A3B8"))
