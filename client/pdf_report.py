import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

NAVY = colors.HexColor("#1B2A4A")
BLUE = colors.HexColor("#2563EB")
ORANGE = colors.HexColor("#F59E0B")
GREEN = colors.HexColor("#10B981")
RED = colors.HexColor("#EF4444")
LIGHT = colors.HexColor("#F0F4FA")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=NAVY, fontSize=20, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9)
SMALL = ParagraphStyle("small", parent=styles["BodyText"], fontSize=7.5, textColor=colors.HexColor("#64748B"))


def _status_color(status):
    return {
        "laufend": GREEN, "kritisch": RED, "geplant": BLUE, "abgeschlossen": colors.HexColor("#6B7280"),
    }.get(status, BLUE)


def _fmt_eur(v):
    return f"{(v or 0):,.0f} €".replace(",", ".")


def _fmt_pct(v):
    return f"{(v or 0)*100:.0f} %"


def _kpi_table(kpis, labels=None):
    labels = labels or [
        ("count", "Projekte gesamt"), ("running", "Laufend"), ("critical", "Kritisch"),
        ("planned", "Geplant"), ("done", "Abgeschlossen"),
    ]
    row1 = [Paragraph(l, ParagraphStyle("k", parent=SMALL, textColor=colors.white, fontSize=8)) for _, l in labels]
    row2 = [Paragraph(str(kpis.__dict__.get(k, "")) if not isinstance(kpis.__dict__.get(k, ""), float)
                      else f"{kpis.__dict__[k]:.2f}",
                      ParagraphStyle("v", parent=BODY, fontSize=13, textColor=NAVY, alignment=1))
            for k, _ in labels]
    t = Table([row1, row2], colWidths=[38 * mm] * len(labels))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15 * mm, 10 * mm, "ProjectDash – Kältetechnik Projektcontrolling")
    canvas.drawRightString(285 * mm, 10 * mm, f"Erstellt am {date.today().strftime('%d.%m.%Y')} | Seite {doc.page}")
    canvas.restoreState()


def portfolio_report(path, portfolio, title="Projektübersicht – Soll/Ist-Vergleich"):
    doc = SimpleDocTemplate(path, pagesize=landscape(A4), title=title,
                           leftMargin=12 * mm, rightMargin=12 * mm, topMargin=14 * mm, bottomMargin=16 * mm)
    story = [Paragraph(title, H1),
             Paragraph(f"Stand {date.today().strftime('%d.%m.%Y')} | {portfolio.count} Projekte", SMALL),
             Spacer(1, 6)]
    story.append(_kpi_table(portfolio))
    story.append(Spacer(1, 8))

    header = ["Projekt", "Status", "Fortschritt Soll/Ist", "Ende Soll / Prognose",
              "Budget", "Ist-Kosten", "Prognose", "Δ Budget", "CPI", "SPI"]
    rows = [header]
    for i in sorted(portfolio.items, key=lambda x: x.project.get("code", "")):
        p = i.project
        delta = f"+{_fmt_eur(abs(i.vac))}" if i.vac < 0 else f"{_fmt_eur(i.vac)}"
        rows.append([
            Paragraph(f"{p.get('code')}<br/><b>{p.get('name')}</b>", ParagraphStyle("p", parent=BODY, fontSize=8)),
            Paragraph(p.get("status", ""), ParagraphStyle("s", parent=BODY, fontSize=8,
                     textColor=_status_color(p.get("status")))),
            f"{_fmt_pct(i.p_plan)} / {_fmt_pct(i.p_act)}",
            Paragraph(f"{(p.get('end_plan') or '')[:10]}<br/>{(i.project.get('end_forecast') or p.get('end_plan') or '')[:10]}",
                      ParagraphStyle("d", parent=BODY, fontSize=8, alignment=1)),
            _fmt_eur(i.budget), _fmt_eur(i.cost_actual), _fmt_eur(i.eac),
            delta, f"{i.cpi:.2f}", f"{i.spi:.2f}",
        ])
    t = Table(rows, colWidths=[62 * mm] + [20 * mm] * 9, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D3E4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (9, 1), (9, -1), "CENTER"),
    ]))
    story.append(t)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def project_report(path, kpi_item, phases, milestones, costs, hours):
    p = kpi_item.project
    doc = SimpleDocTemplate(path, pagesize=A4, title=f"Projektbericht {p.get('code')}",
                           leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm, bottomMargin=16 * mm)
    forecast = p.get("end_forecast") or ""
    forecast_note = f" (Prognose: {forecast})" if forecast and forecast != p.get("end_plan") else ""
    story = [
        Paragraph(f"{p.get('code')} \u2013 {p.get('name')}", H1),
        Paragraph(f"{p.get('description', '')}", BODY),
        Spacer(1, 4),
        Paragraph(f"Status: <b>{p.get('status')}</b> | Priorität: {p.get('priority')} | "
                  f"Ort: {p.get('location')} | Projektleitung: {p.get('manager')}<br/>"
                  f"Zeitraum: {p.get('start_plan')} – {p.get('end_plan')}{forecast_note}", BODY),
        Spacer(1, 8),
        Paragraph("Kennzahlen", H2),
    ]
    kpis = [("Budget", kpi_item.budget), ("Plan bis heute", kpi_item.pv),
            ("Ist-Kosten", kpi_item.cost_actual), ("Earned Value", kpi_item.ev),
            ("Prognose Endkosten (EAC)", kpi_item.eac), ("\u0394 Budget (VAC)", kpi_item.vac),
            ("CPI", kpi_item.cpi), ("SPI", kpi_item.spi),
            ("Fortschritt Soll", kpi_item.p_plan), ("Fortschritt Ist", kpi_item.p_act),
            ("Stunden Soll", kpi_item.hours_plan), ("Stunden Ist", kpi_item.hours_actual)]
    formatter = {
        "CPI": lambda v: f"{v:.2f}", "SPI": lambda v: f"{v:.2f}",
        "Fortschritt Soll": _fmt_pct, "Fortschritt Ist": _fmt_pct,
        "Stunden Soll": lambda v: f"{v:,.0f} h", "Stunden Ist": lambda v: f"{v:,.0f} h",
        "\u0394 Budget (VAC)": lambda v: (f"+{_fmt_eur(-v)}" if v < 0 else _fmt_eur(v)),
    }
    row1 = [Paragraph(k, ParagraphStyle("k", parent=SMALL, fontSize=8, textColor=colors.white)) for k, _ in kpis]
    row2 = [Paragraph(formatter.get(k, _fmt_eur)(v),
                      ParagraphStyle("v", parent=BODY, fontSize=11, alignment=1))
            for k, v in kpis]
    t = Table([row1, row2], colWidths=[30 * mm] * 6)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)

    story.append(Paragraph("Terminplan (Phasen)", H2))
    ph = [["Phase", "Beginn Soll", "Ende Soll", "Beginn Ist", "Ende Ist"]]
    for ph_row in phases:
        ph.append([ph_row.get("name", ""), ph_row.get("start_plan", ""), ph_row.get("end_plan", ""),
                   ph_row.get("start_actual") or "–", ph_row.get("end_actual") or "–"])
    story.append(Table(ph, colWidths=[50 * mm] + [35 * mm] * 4))

    story.append(Paragraph("Meilensteine", H2))
    ms = [["Meilenstein", "Datum Soll", "Datum Ist", "Status"]]
    for m in milestones:
        ms.append([m.get("name", ""), m.get("date_plan", ""), m.get("date_actual") or "–",
                   "erreicht" if m.get("date_actual") else "offen"])
    story.append(Table(ms, colWidths=[70 * mm] + [30 * mm] * 3))

    story.append(Paragraph("Kosten (Soll/Ist je Kategorie)", H2))
    ko = [["Kategorie", "Datum", "Soll (EUR)", "Ist (EUR)"]]
    for c in costs:
        ko.append([c.get("category", ""), c.get("date", ""),
                   _fmt_eur(c.get("amount_plan")), _fmt_eur(c.get("amount_actual"))])
    ko.append(["Summe", "", _fmt_eur(kpi_item.cost_plan), _fmt_eur(kpi_item.cost_actual)])
    t = Table(ko, colWidths=[60 * mm, 28 * mm, 45 * mm, 45 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, len(ko) - 1), (-1, len(ko) - 1), LIGHT),
                           ("FONTNAME", (0, len(ko) - 1), (-1, len(ko) - 1), "Helvetica-Bold")]))
    story.append(t)

    story.append(Paragraph("Stunden / Ressourcen", H2))
    st = [["Mitarbeiter", "Funktion", "Soll (h)", "Ist (h)"]]
    for h in hours:
        st.append([h.get("employee", ""), h.get("role", ""),
                   f"{h.get('hours_plan') or 0:,.0f}", f"{h.get('hours_actual') or 0:,.0f}"])
    story.append(Table(st, colWidths=[55 * mm, 55 * mm, 33 * mm, 33 * mm]))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def management_report(path, portfolio):
    doc = SimpleDocTemplate(path, pagesize=landscape(A4), title="Management-Report KPIs",
                           leftMargin=12 * mm, rightMargin=12 * mm, topMargin=14 * mm, bottomMargin=16 * mm)
    story = [Paragraph("Management-Report – Kältetechnik Portfolio-KPIs", H1),
             Paragraph(f"Vertraulich – nur für das Management | Stand {date.today().strftime('%d.%m.%Y')}", SMALL),
             Spacer(1, 6)]
    kpi_labels = [
        ("total_budget", "Gesamtbudget", "eur"), ("total_actual", "Ist-Kosten", "eur"),
        ("total_forecast", "Prognose Endkosten", "eur"), ("forecast_delta", "Δ zum Budget", "eur"),
        ("portfolio_cpi", "Portfolio-CPI", "f2"), ("portfolio_spi", "Portfolio-SPI", "f2"),
        ("total_hours_plan", "Stunden Soll", "h"), ("total_hours_actual", "Stunden Ist", "h"),
    ]
    row1, row2 = [], []
    for key, label, fmt in kpi_labels:
        v = getattr(portfolio, key)
        row1.append(Paragraph(label, ParagraphStyle("k", parent=SMALL, fontSize=8, textColor=colors.white)))
        if fmt == "eur":
            text = _fmt_eur(v) if v >= 0 else f"+{_fmt_eur(-v)}"
        elif fmt == "f2":
            text = f"{v:.2f}"
        else:
            text = f"{v:,.0f} h"
        row2.append(Paragraph(text, ParagraphStyle("v", parent=BODY, fontSize=12, alignment=1)))
    t = Table([row1, row2], colWidths=[34 * mm] * 8)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Projekte mit höchstem Handlungsbedarf (CPI & SPI)", H2))
    rows = [["Projekt", "Status", "Budget", "Ist", "Prognose", "CPI", "SPI", "Terminabweichung (Tage)"]]
    for i in portfolio.worst_projects(10):
        rows.append([f"{i.project.get('code')} {i.project.get('name')}", i.project.get("status", ""),
                     _fmt_eur(i.budget), _fmt_eur(i.cost_actual), _fmt_eur(i.eac),
                     f"{i.cpi:.2f}", f"{i.spi:.2f}", str(i.date_variance)])
    t = Table(rows, colWidths=[80 * mm, 22 * mm] + [30 * mm] * 6, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D3E4")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
