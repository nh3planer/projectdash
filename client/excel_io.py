from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HEAD_FILL = PatternFill("solid", fgColor="1B2A4A")
HEAD_FONT = Font(color="FFFFFF", bold=True, size=11)
ZEBRA = PatternFill("solid", fgColor="F0F4FA")
THIN = Side(style="thin", color="C9D3E4")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

PROJECT_FIELDS = [
    ("code", "Code", 10),
    ("name", "Projektname", 42),
    ("description", "Beschreibung", 46),
    ("size_class", "Größenklasse", 13),
    ("status", "Status", 13),
    ("priority", "Priorität", 11),
    ("location", "Ort", 14),
    ("manager", "Projektleitung", 20),
    ("start_plan", "Start Soll", 13),
    ("end_plan", "Ende Soll", 13),
    ("end_forecast", "Ende Prognose", 14),
    ("budget", "Budget (EUR)", 14),
    ("progress_plan", "Fortschritt Soll", 16),
    ("progress_actual", "Fortschritt Ist", 16),
]

PROJECT_FIELDS_EXPORT = PROJECT_FIELDS + [("id", "ID", 8)]

MILESTONE_FIELDS = [("project_code", "Projekt-Code", 12), ("name", "Meilenstein", 30),
                    ("date_plan", "Datum Soll", 13), ("date_actual", "Datum Ist", 13),
                    ("weight", "Gewicht", 10)]

COST_FIELDS = [("project_code", "Projekt-Code", 12), ("date", "Datum", 13),
               ("category", "Kategorie", 26), ("description", "Beschreibung", 30),
               ("amount_plan", "Kosten Soll (EUR)", 17), ("amount_actual", "Kosten Ist (EUR)", 17)]

HOURS_FIELDS = [("project_code", "Projekt-Code", 12), ("date", "Datum", 13),
                ("employee", "Mitarbeiter", 22), ("role", "Funktion", 22), ("task", "Tätigkeit", 28),
                ("hours_plan", "Stunden Soll", 13), ("hours_actual", "Stunden Ist", 13)]


def _style_sheet(ws, fields):
    for idx, (_, title, width) in enumerate(fields, start=1):
        cell = ws.cell(row=1, column=idx, value=title)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "A2"


def export_workbook(sheets):
    wb = Workbook()
    wb.remove(wb.active)
    for name, fields, rows in sheets:
        ws = wb.create_sheet(name[:31])
        for r_idx, row in enumerate(rows, start=2):
            for c_idx, (key, _, _) in enumerate(fields, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=row.get(key))
                if r_idx % 2 == 0:
                    cell.fill = ZEBRA
                cell.border = BORDER
        _style_sheet(ws, fields)
    return wb


def _read_sheet(ws, fields):
    headers = {}
    for c in range(1, ws.max_column + 1):
        val = ws.cell(row=1, column=c).value
        if val:
            headers[str(val).strip().lower()] = c
    rows = []
    for r in range(2, ws.max_row + 1):
        row = {}
        empty = True
        for key, title, _ in fields:
            col = headers.get(title.lower())
            if col is None:
                continue
            v = ws.cell(row=r, column=col).value
            if v is not None and str(v).strip() != "":
                empty = False
                if isinstance(v, date):
                    v = v.isoformat()
            row[key] = v
        if not empty:
            rows.append(row)
    return rows


def import_workbook(path):
    from openpyxl import load_workbook

    wb = load_workbook(path, data_only=True)
    result = {}
    mapping = [
        ("Projekte", PROJECT_FIELDS, "projects"),
        ("Meilensteine", MILESTONE_FIELDS, "milestones"),
        ("Kosten", COST_FIELDS, "cost_entries"),
        ("Stunden", HOURS_FIELDS, "hours_entries"),
    ]
    for ws in wb.worksheets:
        for title, fields, table in mapping:
            if ws.title.strip().lower() == title.lower():
                result[table] = _read_sheet(ws, fields)
    if "projects" not in result:
        for ws in wb.worksheets:
            lower = [str(ws.cell(row=1, column=c).value or "").lower() for c in range(1, ws.max_column + 1)]
            if "code" in lower and "projektname" in lower:
                result["projects"] = _read_sheet(ws, PROJECT_FIELDS)
                break
    return result
