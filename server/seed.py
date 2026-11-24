import sys
from datetime import date, timedelta

from server import auth
from server.database import utcnow

TODAY = date.today()


def d(days):
    return (TODAY + timedelta(days=days)).isoformat()


PROJECTS = [
    {
        "code": "K-1001", "name": "Tiefkühllager Logistikzentrum Nord",
        "description": "NH3/CO2-Kaskadenanlage für Tiefkühl- und Frischebereich, 1,2 MW Kälteleistung",
        "size_class": "gross", "status": "kritisch", "priority": "hoch", "location": "Hamburg",
        "manager": "Anna Kaltenbrunn", "start": d(-120), "end_plan": d(85), "forecast": d(100),
        "budget": 4800000.0, "p_plan": 0.59, "p_act": 0.48,
        "current": 3266300.0,
        "cost_categories": [("Planung & Auslegung", 320000, 305000), ("Material Verdichter/Maschinenraum", 1850000, 1720000), ("Rohrleitungen & Isolierung", 620000, 665000), ("MSR-Technik & Elektro", 780000, 571300)],
        "hours": [("Anna Kaltenbrunn", "Projektleitung", 1200, 980), ("Dipl.-Ing. Stefan Froster", "Planung/Auslegung", 900, 840), ("Maikel Eisfeld", "Montage", 3200, 2450)],
    },
    {
        "code": "K-1002", "name": "Supermarkt-Kälteanlage Filiale 47",
        "description": "Neubau SB-Kühlmoebel-Zentralkälteanlage mit CO2-Transkritsystem und Wärmerückgewinnung",
        "size_class": "klein", "status": "abgeschlossen", "priority": "normal", "location": "Dortmund",
        "manager": "Ben Kühlmann", "start": d(-190), "end_plan": d(-60), "forecast": d(-60),
        "budget": 85000.0, "p_plan": 1.0, "p_act": 1.0,
        "current": 79400.0,
        "cost_categories": [("Material & Verdichter", 46000, 43800), ("Montage & Inbetriebnahme", 32000, 30600), ("Planung", 7000, 5000)],
        "hours": [("Ben Kühlmann", "Projektleitung & Montage", 220, 225), ("Lea Frost", "Montage", 160, 149)],
    },
    {
        "code": "K-1003", "name": "Wärmepumpe Bürokomplex West",
        "description": "Klimaanzeige Zusatzheizung: Erdgekoppelte Großwärmepumpe 260 kW für Bürogebäude",
        "size_class": "mittel", "status": "laufend", "priority": "normal", "location": "Köln",
        "manager": "Clara Neumann", "start": d(-80), "end_plan": d(45), "forecast": d(45),
        "budget": 260000.0, "p_plan": 0.29, "p_act": 0.29,
        "current": 46880.0,
        "cost_categories": [("Wärmepumpen-Aggregate", 145000, 37000), ("Erdreichsonden & Anbindung", 62000, 7000), ("Planung", 30000, 2880), ("Montage", 23000, 0)],
        "hours": [("Clara Neumann", "Projektleitung", 260, 78), ("Tobias Wärm", "Planung", 300, 92)],
    },
    {
        "code": "K-1004", "name": "Retrofit Kühlhaus Süd",
        "description": "Umrüstung R404A auf CO2-Verdampferdruck, Austausch von 6 Verdichtern",
        "size_class": "klein", "status": "kritisch", "priority": "hoch", "location": "München",
        "manager": "Ben Kühlmann", "start": d(-100), "end_plan": d(10), "forecast": d(18),
        "budget": 180000.0, "p_plan": 0.29, "p_act": 0.26,
        "current": 61200.0,
        "cost_categories": [("Verdichtersatz", 90000, 6400), ("Umrüstung MSR & Sicherheitstechnik", 45000, 31200), ("Montage & Inbetriebnahme", 35000, 23600)],
        "hours": [("Ben Kühlmann", "Projektleitung", 180, 96), ("Maikel Eisfeld", "Montage", 420, 238)],
    },
    {
        "code": "K-1005", "name": "Prozesskühlung Brauerei Ost",
        "description": "Glykol-Kreislauf mit Windkessel und 9-körper Plattenkühler, 450 kW",
        "size_class": "mittel", "status": "laufend", "priority": "normal", "location": "Bamberg",
        "manager": "Dipl.-Ing. Stefan Froster", "start": d(-140), "end_plan": d(30), "forecast": d(30),
        "budget": 620000.0, "p_plan": 0.71, "p_act": 0.71,
        "current": 398400.0,
        "cost_categories": [("Plattenkühler & Pumpen", 280000, 261000), ("Rohrleitungsbau", 150000, 121400), ("MSR & Leittechnik", 90000, 16000), ("Planung", 40000, 0)],
        "hours": [("Dipl.-Ing. Stefan Froster", "Projektleitung", 320, 216), ("Lea Frost", "Montage", 780, 704)],
    },
    {
        "code": "K-1006", "name": "Kältezentrale Pharmapark Basel",
        "description": "Hochverfügbares redundant ausgelegtes Kältenetz (2x100%) für Labor- und Produktionsgebäude, 2,4 MW",
        "size_class": "gross", "status": "laufend", "priority": "hoch", "location": "Basel",
        "manager": "Anna Kaltenbrunn", "start": d(-60), "end_plan": d(210), "forecast": d(210),
        "budget": 7800000.0, "p_plan": 0.14, "p_act": 0.16,
        "current": 1248000.0,
        "cost_categories": [("Grundplanung & Genehmigung", 420000, 418000), ("Kältemaschinen n+1", 4200000, 530000), ("Kältnetz & Pumpgruppen", 1800000, 300000), ("MSR-Technik", 900000, 0)],
        "hours": [("Anna Kaltenbrunn", "Projektleitung", 1400, 192), ("Dipl.-Ing. Stefan Froster", "Planung", 1100, 208)],
    },
    {
        "code": "K-1007", "name": "Eisbahn Kühlfeld Regen",
        "description": "Sole-Großkühlteiche und Kältetechnik für Kunsteisbahn mit redundantem Solekreislauf, 380 kW",
        "size_class": "mittel", "status": "geplant", "priority": "normal", "location": "Regensburg",
        "manager": "Clara Neumann", "start": d(20), "end_plan": d(180), "forecast": None,
        "budget": 410000.0, "p_plan": 0.0, "p_act": 0.0,
        "current": 0.0,
        "cost_categories": [("Soleverdichter & Kühlfeld", 220000, 0), ("Montage", 120000, 0), ("Planung", 70000, 0)],
        "hours": [("Clara Neumann", "Projektleitung", 220, 0), ("Tobias Wärm", "Planung", 380, 0)],
    },
    {
        "code": "K-1008", "name": "Rechenzentrum Abwärme REC-1",
        "description": "Freikühlung und Wärmerückgewinnung aus Rechenzentrum in Fernwärmenetz, 1,8 MW",
        "size_class": "gross", "status": "kritisch", "priority": "hoch", "location": "Frankfurt",
        "manager": "Dipl.-Ing. Stefan Froster", "start": d(-220), "end_plan": d(60), "forecast": d(95),
        "budget": 3200000.0, "p_plan": 0.83, "p_act": 0.74,
        "current": 2465000.0,
        "cost_categories": [("Freikühler & Racks", 1450000, 1310000), ("Wärmepumpen & Netzanbindung", 1100000, 1000000), ("Planung & Bauleitung", 420000, 155000), ("MSR-Technik", 230000, 0)],
        "hours": [("Dipl.-Ing. Stefan Froster", "Projektleitung", 900, 652), ("Maikel Eisfeld", "Montage", 2200, 1608), ("Lea Frost", "Montage", 1500, 1010)],
    },
    {
        "code": "K-1009", "name": "Bäckerei Kühltheke Kette XY",
        "description": "Rollout von Thermo-Kühltheeken in 8 Filialen inkl. verbundener Zentralsteuerung",
        "size_class": "klein", "status": "laufend", "priority": "niedrig", "location": "Bremen",
        "manager": "Ben Kühlmann", "start": d(-40), "end_plan": d(50), "forecast": d(50),
        "budget": 120000.0, "p_plan": 0.37, "p_act": 0.40,
        "current": 39600.0,
        "cost_categories": [("Kühltheeken & Regale", 78000, 31200), ("Montage & Elektro", 32000, 8400), ("Planung", 10000, 0)],
        "hours": [("Ben Kühlmann", "Projektleitung", 120, 48), ("Lea Frost", "Montage", 280, 104)],
    },
    {
        "code": "K-1010", "name": "Malzsilokühlung Mälzerei Nord",
        "description": "Luftkonditionierung und Kühlung von 4 Malzsilos mit Klimakanonensystem, 240 kW",
        "size_class": "mittel", "status": "abgeschlossen", "priority": "normal", "location": "Schwerin",
        "manager": "Clara Neumann", "start": d(-300), "end_plan": d(-130), "forecast": d(-133),
        "budget": 350000.0, "p_plan": 1.0, "p_act": 1.0,
        "current": 308500.0,
        "cost_categories": [("Klimakästen & Ventilatoren", 175000, 170000), ("Rohrleitungen & Dämmung", 85000, 77500), ("MSR", 50000, 39500), ("Planung", 40000, 21500)],
        "hours": [("Clara Neumann", "Projektleitung", 300, 310), ("Maikel Eisfeld", "Montage", 640, 655)],
    },
]

PHASE_TEMPLATE = [
    ("Planung & Auslegung", 0.00, 0.14),
    ("Beschaffung", 0.12, 0.34),
    ("Montage", 0.32, 0.68),
    ("Inbetriebnahme", 0.66, 0.82),
    ("Dokumentation", 0.80, 0.93),
    ("Abnahme", 0.92, 1.00),
]

MILESTONE_TEMPLATE = [
    ("Planung freigegeben", 0.14),
    ("Anlagenkomponenten geliefert", 0.34),
    ("Montage abgeschlossen", 0.68),
    ("Inbetriebnahme abgeschlossen", 0.82),
    ("Abnahme protokolliert", 1.00),
]


def _duration_days(p):
    from datetime import datetime

    start = datetime.fromisoformat(p["start"]).date()
    end = datetime.fromisoformat(p["end_plan"]).date()
    return (end - start).days


def _seed_project(db, p):
    now = utcnow()
    dur = _duration_days(p)
    cur = db.conn.execute(
        """INSERT INTO projects (code, name, description, size_class, status, priority,
           location, manager, start_plan, end_plan, end_forecast, budget,
           progress_plan, progress_actual, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (p["code"], p["name"], p["description"], p["size_class"], p["status"], p["priority"],
         p["location"], p["manager"], p["start"], p["end_plan"], p.get("forecast"),
         p["budget"], p["p_plan"], p["p_act"], now),
    )
    pid = cur.lastrowid

    start = p["start"]
    for idx, (name, f_from, f_to) in enumerate(PHASE_TEMPLATE):
        s = d(_offset_days(p, f_from, dur))
        e = d(_offset_days(p, f_to, dur))
        s_act, e_act = s, None
        if p["p_act"] >= f_from:
            s_act = s
        elif p["p_act"] > 0 and idx == 0:
            s_act = s
        if p["p_act"] >= f_to:
            e_act = e
        db.conn.execute(
            "INSERT INTO phases (project_id, name, start_plan, end_plan, start_actual, end_actual, sort_order, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (pid, name, s, e, s_act, e_act, idx, now),
        )

    for name, frac in MILESTONE_TEMPLATE:
        plan = d(_offset_days(p, frac, dur))
        actual = plan if p["p_act"] >= frac else None
        if p["status"] == "kritisch" and frac >= 0.68 and p["p_act"] < frac:
            actual = None
        db.conn.execute(
            "INSERT INTO milestones (project_id, name, date_plan, date_actual, weight, updated_at) VALUES (?,?,?,?,?,?)",
            (pid, name, plan, actual, frac, now),
        )

    for cat, plan, act in p["cost_categories"]:
        db.conn.execute(
            "INSERT INTO cost_entries (project_id, date, category, description, amount_plan, amount_actual, updated_at) VALUES (?,?,?,?,?,?,?)",
            (pid, start, cat, cat, plan, act, now),
        )

    for emp, role, plan, act in p["hours"]:
        db.conn.execute(
            "INSERT INTO hours_entries (project_id, date, employee, role, task, hours_plan, hours_actual, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (pid, start, emp, role, role, plan, act, now),
        )
    return pid


def _offset_days(p, fraction, dur):
    from datetime import datetime

    start = datetime.fromisoformat(p["start"]).date()
    target = start + timedelta(days=int(dur * fraction))
    return (target - TODAY).days


def run(db):
    now = utcnow()
    users = [
        ("admin", "Admin Administrator", "admin", "admin@projectdash.local", "admin"),
        ("geschaeftsfuehrung", "Greta Geschäftsführung", "management", "gf@projectdash.local", "management123"),
        ("kaltenbrunn", "Anna Kaltenbrunn", "projektleiter", "anna.k@projectdash.local", "projekt123"),
        ("kuehlmann", "Ben Kühlmann", "projektleiter", "ben.k@projectdash.local", "projekt123"),
        ("froster", "Stefan Froster", "mitarbeiter", "stefan.f@projectdash.local", "mitarbeit123"),
        ("eisfeld", "Maikel Eisfeld", "mitarbeiter", "maikel.e@projectdash.local", "mitarbeit123"),
        ("gast", "Günter Gast", "gast", "gast@projectdash.local", "gast123"),
    ]
    for username, full_name, role, email, password in users:
        db.conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role, email, active, updated_at) VALUES (?,?,?,?,?,1,?)",
            (username, auth.hash_password(password), full_name, role, email, now),
        )
    for p in PROJECTS:
        _seed_project(db, p)
    db.conn.commit()


if __name__ == "__main__":
    from server.database import CentralDB

    db = CentralDB(sys.argv[1] if len(sys.argv) > 1 else "central.db")
    print("Seed complete:", db.path)
