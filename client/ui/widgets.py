from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                                QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
                                QStyledItemDelegate, QStyleOptionViewItem)

from client.theme import STATUS_COLORS, SIZE_LABELS


def fmt_eur(v, compact=False):
    if v is None:
        v = 0
    s = f"{abs(v):,.0f}".replace(",", ".")
    sign = "-" if v < 0 else ""
    if compact and abs(v) >= 1_000_000:
        return f"{sign}{abs(v)/1_000_000:.2f} Mio €"
    if compact and abs(v) >= 1000:
        return f"{sign}{abs(v)/1000:.1f} T€"
    return f"{sign}{s} €"


def fmt_pct(v):
    return f"{(v or 0)*100:.0f} %"


class Card(QFrame):
    def __init__(self, title, value, sub="", color="#F8FAFC", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("kpiTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("kpiValue")
        self.value_label.setStyleSheet(f"color: {color};")
        self.sub_label = QLabel(sub)
        self.sub_label.setObjectName("kpiSub")
        self.sub_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.sub_label)

    def set_value(self, value, sub="", color=None):
        self.value_label.setText(value)
        if color:
            self.value_label.setStyleSheet(f"color: {color};")
        self.sub_label.setText(sub)


class StatusBadge(QLabel):
    def __init__(self, status, parent=None):
        super().__init__(status.capitalize(), parent)
        self.setObjectName("badge")
        fg, bg = STATUS_COLORS.get(status, ("#E2E8F0", "#1E293B"))
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; font-weight: 700;"
        )
        self.setAlignment(Qt.AlignCenter)


class ProgressPair(QWidget):
    def __init__(self, p_plan, p_act, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        bar = self._bar(p_act, self._cls(p_act, p_plan))
        plan = QLabel(f"Soll {fmt_pct(p_plan)}")
        plan.setStyleSheet("color: #64748B; font-size: 9px;")
        layout.addWidget(bar)
        layout.addWidget(plan)

    def _cls(self, act, plan):
        if act + 0.02 >= plan:
            return "ok"
        if act + 0.15 >= plan:
            return "warn"
        return "bad"

    def _bar(self, val, cls):
        b = QProgressBar()
        b.setObjectName(cls if cls != "ok" else "ok")
        b.setRange(0, 100)
        b.setValue(int(max(0, min(1, val)) * 100))
        b.setFormat(f"{fmt_pct(val)}")
        b.setTextVisible(True)
        b.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: "
            f"{'#10B981' if cls == 'ok' else '#F59E0B' if cls == 'warn' else '#EF4444'}; }}"
        )
        return b


class GanttWidget(QWidget):
    def __init__(self, phases, start=None, end=None, parent=None):
        super().__init__(parent)
        self.phases = phases or []
        self.start = start
        self.end = end
        self.setMinimumHeight(max(120, len(self.phases) * 34 + 30))
        self.row_h = 30
        self.header_h = 24

    def _range(self):
        if not self.phases:
            return None, None
        dates = []
        for ph in self.phases:
            for k in ("start_plan", "end_plan", "start_actual", "end_actual"):
                if ph.get(k):
                    dates.append(str(ph[k])[:10])
        if not dates:
            return None, None
        lo, hi = min(dates), max(dates)
        if self.start:
            lo = min(lo, str(self.start)[:10])
        if self.end:
            hi = max(hi, str(self.end)[:10])
        from datetime import date, datetime, timedelta

        d_lo = datetime.fromisoformat(lo).date()
        d_hi = datetime.fromisoformat(hi).date()
        pad = max(1, (d_hi - d_lo).days // 20)
        return d_lo - timedelta(days=pad), d_hi + timedelta(days=pad)

    def paintEvent(self, event):
        if not self.phases:
            return
        from datetime import date, datetime

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        lo, hi = self._range()
        if not lo or not hi:
            painter.end()
            return
        total = max(1, (hi - lo).days)
        w = self.width() - 180
        chart_h = self.height() - self.header_h
        today = date.today()
        bg = QColor("#0B1220")
        painter.fillRect(0, 0, self.width(), self.height(), bg)
        painter.setPen(QPen(QColor("#1E293B"), 1))
        months = set()
        for i in range(0, total + 1, max(1, total // 14)):
            d = lo.replace() + __import__("datetime").timedelta(days=i)
            months.add((d.year, d.month))
        for year, month in sorted(months):
            d = date(year, month, 1)
            if d < lo or d > hi:
                continue
            x = 180 + w * ((d - lo).days / total)
            painter.setPen(QColor("#334155"))
            painter.drawLine(int(x), self.header_h, int(x), self.height() - 4)
            painter.setPen(QColor("#94A3B8"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(int(x) + 3, 14, f"{month:02d}/{str(year)[2:]}")
        for idx, ph in enumerate(self.phases):
            y = self.header_h + idx * self.row_h + 4
            painter.setPen(QColor("#CBD5E1"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(6, y + 13, str(ph.get("name", ""))[:24])
            ps, pe = str(ph.get("start_plan"))[:10], str(ph.get("end_plan"))[:10]
            if ps and pe:
                x1 = 180 + w * ((datetime.fromisoformat(ps).date() - lo).days / total)
                x2 = 180 + w * ((datetime.fromisoformat(pe).date() - lo).days / total)
                rect = QRectF(x1, y, max(4, x2 - x1), 14)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#2563EB", 210)))
                painter.drawRoundedRect(rect, 4, 4)
            as_, ae = ph.get("start_actual"), ph.get("end_actual")
            if as_:
                a1 = 180 + w * ((datetime.fromisoformat(str(as_)[:10]).date() - lo).days / total)
                end_date = datetime.fromisoformat(str(ae)[:10]).date() if ae else min(today, hi)
                a2 = 180 + w * max(0.02, ((end_date - lo).days / total))
                rect = QRectF(a1, y + 8, max(4, a2 - a1), 10)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#F59E0B", 230)))
                painter.drawRoundedRect(rect, 4, 4)
        if lo <= today <= hi:
            tx = 180 + w * ((today - lo).days / total)
            painter.setPen(QPen(QColor("#EF4444"), 2))
            painter.drawLine(int(tx), self.header_h - 2, int(tx), self.height() - 4)
            painter.setPen(QColor("#EF4444"))
            painter.drawText(int(tx) - 18, self.header_h - 4, "Heute")
        painter.end()


class ProjectTable(QTableWidget):
    HEADERS = ["Projekt", "Status", "Fortschritt Soll / Ist", "Ende Soll",
               "Prognose", "Termin", "Budget", "Ist-Kosten", "Δ Budget", "CPI"]

    def __init__(self, show_costs=True, parent=None):
        super().__init__(0, len(self.HEADERS), parent)
        self.show_costs = show_costs
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(False)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 90)
        self.setColumnWidth(2, 140)
        self.setColumnWidth(3, 90)
        self.setColumnWidth(4, 90)
        self.setColumnWidth(5, 90)
        if show_costs:
            self.setColumnWidth(6, 110)
            self.setColumnWidth(7, 110)
            self.setColumnWidth(8, 110)
            self.setColumnWidth(9, 60)
        else:
            for col in (6, 7, 8, 9):
                self.hideColumn(col)
        self.doubleClicked.connect(lambda idx: self._emit_open(idx))
        self.open_requested = None

    def _emit_open(self, index):
        item = self.item(index.row(), 0)
        if item and self.open_requested:
            self.open_requested(item.data(Qt.UserRole))

    def fill(self, items):
        self.setRowCount(0)
        for item in items:
            k = item
            p = k.project
            row = self.rowCount()
            self.insertRow(row)
            name = QTableWidgetItem(f"{p.get('code')}  ·  {p.get('name')}")
            name.setData(Qt.UserRole, p["id"])
            name.setToolTip(f"{p.get('description', '')}\nGröße: {SIZE_LABELS.get(p.get('size_class'), p.get('size_class'))} | PL: {p.get('manager')}")
            self.setItem(row, 0, name)
            badge = QTableWidgetItem(p.get("status", "").capitalize())
            badge.setForeground(QColor({"laufend": "#10B981", "kritisch": "#EF4444",
                                        "geplant": "#3B82F6", "abgeschlossen": "#6B7280"}.get(p.get("status"), "#CBD5E1")))
            self.setItem(row, 1, badge)
            self.setCellWidget(row, 2, ProgressPair(k.p_plan if hasattr(k, "p_plan") else 0,
                                                    k.p_act if hasattr(k, "p_act") else 0))
            self.setItem(row, 3, QTableWidgetItem(str(p.get("end_plan") or "")[:10] or "–"))
            self.setItem(row, 4, QTableWidgetItem(str(p.get("end_forecast") or "")[:10] or "–"))
            td = k.date_variance if hasattr(k, "date_variance") else 0
            titem = QTableWidgetItem(f"{td:+d} T" if td else "im Plan")
            if td > 0:
                titem.setForeground(QColor("#EF4444"))
            elif td < 0:
                titem.setForeground(QColor("#10B981"))
            self.setItem(row, 5, titem)
            if self.show_costs:
                self.setItem(row, 6, QTableWidgetItem(fmt_eur(k.budget, compact=True)))
                self.setItem(row, 7, QTableWidgetItem(fmt_eur(k.cost_actual, compact=True)))
                vac = k.vac
                vitem = QTableWidgetItem(fmt_eur(vac, compact=True))
                vitem.setForeground(QColor("#10B981" if vac >= 0 else "#EF4444"))
                self.setItem(row, 8, vitem)
                citem = QTableWidgetItem(f"{k.cpi:.2f}")
                citem.setForeground(QColor("#EF4444" if k.cpi < 0.95 else "#10B981"))
                self.setItem(row, 9, citem)
        self.sortItems(0)
