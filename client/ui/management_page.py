from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QHeaderView, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from client.kpi import PortfolioKPI
from client.ui.widgets import Card, fmt_eur


class ManagementPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName("root")
        self.portfolio = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        head = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Management-Cockpit")
        title.setObjectName("h1")
        sub = QLabel("Vertrauliche KPIs – sichtbar nur für Management und Administration")
        sub.setObjectName("muted")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        sub2 = QLabel("")
        sub2.setObjectName("muted")
        head.addLayout(title_box)
        head.addStretch(1)
        btn_pdf = QPushButton("Management Report (PDF)")
        btn_pdf.setObjectName("danger")
        btn_pdf.clicked.connect(self._export_pdf)
        btn_xlsx = QPushButton("Excel Export")
        btn_xlsx.clicked.connect(self._export_excel)
        head.addWidget(btn_xlsx)
        head.addWidget(btn_pdf)
        root.addLayout(head)

        self.cards = QHBoxLayout()
        self.cards.setSpacing(12)
        self.kpi_cards = [
            Card("Portfolio CPI", "–", "Kosteneffizienz gesamt"),
            Card("Portfolio SPI", "–", "Termineffizienz gesamt"),
            Card("Δ Prognose zum Budget", "–", "Gesamtrisiko in €"),
            Card("Problemprojekte", "–", "CPI < 0.95 oder Termin verspätet"),
            Card("Stundenverbrauch", "–", "Ist ggü. Soll"),
        ]
        for c in self.kpi_cards:
            self.cards.addWidget(c)
        root.addLayout(self.cards)

        body = QHBoxLayout()
        body.setSpacing(14)
        left = QVBoxLayout()
        ranking_label = QLabel("Projekt-Ranking nach Risiko (CPI + SPI)")
        ranking_label.setObjectName("h2")
        left.addWidget(ranking_label)
        self.rank_table = QTableWidget(0, 7)
        self.rank_table.setHorizontalHeaderLabels(["Projekt", "CPI", "SPI", "Budget", "Ist", "Prognose", "Δ Budget"])
        self.rank_table.verticalHeader().setVisible(False)
        self.rank_table.setAlternatingRowColors(True)
        self.rank_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rank_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        left.addWidget(self.rank_table)
        body.addLayout(left, 3)

        right = QVBoxLayout()
        self.chart_panel = QWidget()
        right.addWidget(QLabel("Portfolio-Budgetverteilung (T€)", objectName="h2"))
        self.chart_host = QWidget()
        right.addWidget(self.chart_host, 1)
        body.addLayout(right, 2)
        root.addLayout(body, 1)

    def _export_pdf(self):
        from client import pdf_report

        path, _ = QFileDialog.getSaveFileName(self, "Management-Report speichern",
                                               "management_report.pdf", "PDF (*.pdf)")
        if path and self.portfolio:
            pdf_report.management_report(path, self.portfolio)
            self.app.status(f"Management-Report gespeichert: {path}")

    def _export_excel(self):
        self.app.export_excel()

    def refresh(self):
        if not self.app.db.has_data():
            return
        projects = self.app.db.projects()
        costs_by_pid, hours_by_pid = {}, {}
        for c in self.app.db.rows("cost_entries"):
            costs_by_pid.setdefault(c["project_id"], []).append(c)
        for h in self.app.db.rows("hours_entries"):
            hours_by_pid.setdefault(h["project_id"], []).append(h)
        self.portfolio = PortfolioKPI(projects, costs_by_pid, hours_by_pid)
        pf = self.portfolio
        self.kpi_cards[0].set_value(f"{pf.portfolio_cpi:.2f}",
                                    "unter 1.0 = über Budget", color="#EF4444" if pf.portfolio_cpi < 1 else "#10B981")
        self.kpi_cards[1].set_value(f"{pf.portfolio_spi:.2f}",
                                    "unter 1.0 = hinter dem Plan", color="#EF4444" if pf.portfolio_spi < 1 else "#10B981")
        fd = pf.forecast_delta
        self.kpi_cards[2].set_value(("+" if fd > 0 else "") + fmt_eur(fd, compact=True),
                                    f"Budget: {fmt_eur(pf.total_budget, compact=True)} | Prognose: {fmt_eur(pf.total_forecast, compact=True)}",
                                    color="#EF4444" if fd > 0 else "#10B981")
        problems = [i for i in pf.items if (i.cpi < 0.95 or i.date_variance > 0) and i.project.get("status") != "abgeschlossen"]
        self.kpi_cards[3].set_value(str(len(problems)),
                                    "…" if not problems else ", ".join(i.project.get("code") for i in problems[:4]),
                                    color="#EF4444" if problems else "#10B981")
        hh = pf.total_hours_actual - pf.total_hours_plan
        self.kpi_cards[4].set_value(f"{pf.total_hours_actual:,.0f} h".replace(",", "."),
                                    f"{'+' if hh > 0 else ''}{hh:,.0f} h ggü. Soll ({pf.total_hours_plan:,.0f} h)".replace(",", "."),
                                    color="#F59E0B" if hh > 0 else "#10B981")

        self.rank_table.setRowCount(0)
        for i in sorted(pf.items, key=lambda x: x.cpi + x.spi):
            row = self.rank_table.rowCount()
            self.rank_table.insertRow(row)
            self.rank_table.setItem(row, 0, QTableWidgetItem(f"{i.project.get('code')} · {i.project.get('name')}"))
            for col, val in enumerate([f"{i.cpi:.2f}", f"{i.spi:.2f}", fmt_eur(i.budget, compact=True),
                                       fmt_eur(i.cost_actual, compact=True), fmt_eur(i.eac, compact=True),
                                       fmt_eur(i.vac, compact=True)]):
                item = QTableWidgetItem(val)
                if col in (0, 1) and i.cpi < 0.95:
                    item.setForeground(QColor("#EF4444"))
                self.rank_table.setItem(row, col + 1, item)
        self._draw_chart(pf)

    def _draw_chart(self, pf):
        from PySide6.QtCharts import QBarSeries, QBarSet, QCategoryAxis, QChart, QChartView, QValueAxis
        from PySide6.QtWidgets import QVBoxLayout

        layout = self.chart_host.layout() or QVBoxLayout(self.chart_host)
        chart = QChart()
        chart.setBackgroundVisible(False)
        series = QBarSeries()
        plan = QBarSet("Budget (T€)")
        eac = QBarSet("Prognose (T€)")
        cats = QCategoryAxis()
        items = sorted(pf.items, key=lambda i: -i.budget)
        for idx, i in enumerate(items):
            plan.append(round(i.budget / 1000, 0))
            eac.append(round(i.eac / 1000, 0))
            cats.append(i.project.get("code", ""), idx)
        plan.setColor(QColor("#3B82F6"))
        eac.setColor(QColor("#EF4444"))
        series.append(plan)
        series.append(eac)
        chart.addSeries(series)
        chart.createDefaultAxes()
        for axis in list(chart.axes()):
            chart.removeAxis(axis)
        chart.addAxis(cats, __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignBottom)
        val_axis = QValueAxis()
        chart.addAxis(val_axis, __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignLeft)
        series.attachAxis(cats)
        series.attachAxis(val_axis)
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor("#94A3B8"))
        if layout.count():
            old = layout.takeAt(0)
            if old.widget():
                old.widget().deleteLater()
        view = QChartView(chart)
        layout.addWidget(view)
