QSS = """
* { font-family: 'Segoe UI', 'Inter', 'Ubuntu', sans-serif; }
QMainWindow, QWidget#root { background-color: #0F172A; }
QSidebarFrame { background-color: #111C33; border-right: 1px solid #1E2A44; }
QLabel { color: #CBD5E1; font-size: 13px; }
QLabel#h1 { color: #F1F5F9; font-size: 22px; font-weight: 700; }
QLabel#h2 { color: #F8FAFC; font-size: 16px; font-weight: 600; }
QLabel#muted { color: #64748B; font-size: 12px; }
QLabel#brand { color: #FFFFFF; font-size: 16px; font-weight: 800; padding: 6px 4px; }
QPushButton { background-color: #1E293B; color: #E2E8F0; border: 1px solid #334155;
  border-radius: 8px; padding: 7px 14px; font-size: 13px; }
QPushButton:hover { background-color: #273549; border-color: #475569; }
QPushButton#primary { background-color: #2563EB; border: none; color: white; font-weight: 600; }
QPushButton#primary:hover { background-color: #1D4ED8; }
QPushButton#success { background-color: #059669; border: none; color: white; font-weight: 600; }
QPushButton#success:hover { background-color: #047857; }
QPushButton#danger { background-color: #B91C1C; border: none; color: white; font-weight: 600; }
QPushButton#danger:hover { background-color: #991B1B; }
QPushButton#ghost { background-color: transparent; border: 1px solid #334155; }
QLineEdit, QComboBox, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
  background-color: #1E293B; color: #E2E8F0; border: 1px solid #334155;
  border-radius: 8px; padding: 6px 10px; font-size: 13px; selection-background-color: #2563EB; }
QLineEdit:focus, QComboBox:focus { border-color: #2563EB; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #1E293B; color: #E2E8F0;
  selection-background-color: #2563EB; border: 1px solid #334155; }
QTableWidget { background-color: #0B1220; alternate-background-color: #101A2E;
  color: #CBD5E1; gridline-color: #1E293B; border: 1px solid #1E293B;
  border-radius: 10px; font-size: 12px; }
QHeaderView::section { background-color: #111C33; color: #94A3B8; padding: 8px;
  border: none; border-bottom: 1px solid #1E2A44; font-weight: 600; font-size: 12px; }
QTableWidget::item { padding: 4px; }
QTableWidget::item:selected { background-color: #1D4ED8; color: white; }
QProgressBar { background-color: #1E293B; border: none; border-radius: 5px;
  text-align: center; color: #E2E8F0; font-size: 10px; min-height: 10px; max-height: 10px; }
QProgressBar::chunk { background-color: #2563EB; border-radius: 5px; }
QProgressBar#ok::chunk { background-color: #10B981; }
QProgressBar#warn::chunk { background-color: #F59E0B; }
QProgressBar#bad::chunk { background-color: #EF4444; }
QScrollBar:vertical { background: #0B1220; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #334155; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QFrame#card { background-color: #111C33; border: 1px solid #1E2A44; border-radius: 12px; }
QLabel#kpiValue { color: #F8FAFC; font-size: 20px; font-weight: 700; }
QLabel#kpiTitle { color: #94A3B8; font-size: 11px; }
QLabel#kpiSub { color: #64748B; font-size: 10px; }
QPushButton#navBtn { background: transparent; border: none; border-radius: 8px;
  padding: 10px 14px; text-align: left; color: #94A3B8; font-size: 13px; font-weight: 600; }
QPushButton#navBtn:hover { background-color: #1B2A4A; color: #E2E8F0; }
QPushButton#navBtn:checked { background-color: #2563EB; color: white; }
QStatusBar { background-color: #0B1220; color: #64748B; }
QLabel#badge { color: #0B1220; font-size: 10px; font-weight: 700; padding: 2px 0; border-radius: 6px; }
QTabWidget::pane { border: 1px solid #1E2A44; border-radius: 8px; }
QTabBar::tab { background: #111C33; color: #94A3B8; padding: 8px 16px; font-size: 12px;
  border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #1B2A4A; color: #F8FAFC; }
QGroupBox { background-color: #111C33; border: 1px solid #1E2A44; border-radius: 10px;
  margin-top: 14px; padding-top: 10px; color: #CBD5E1; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
QMessageBox, QDialog { background-color: #111C33; color: #E2E8F0; }
QSplitter::handle { background-color: #1E2A44; }
"""

STATUS_COLORS = {
    "laufend": ("#10B981", "#064E3B"),
    "kritisch": ("#EF4444", "#7F1D1D"),
    "geplant": ("#3B82F6", "#1E3A8A"),
    "abgeschlossen": ("#6B7280", "#374151"),
}

SIZE_LABELS = {"klein": "Kleinprojekt", "mittel": "Mittelprojekt", "gross": "Großprojekt"}
SIZE_ORDER = ["klein", "mittel", "gross"]
STATUS_ORDER = ["geplant", "laufend", "kritisch", "abgeschlossen"]
