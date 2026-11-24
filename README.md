# ProjectDash
**Kältetechnik-Projektcontrolling** – moderne Desktop-Anwendung mit zentraler Datenhaltung, Benutzerrechte-Verwaltung, Soll/Ist-Steuerung, Gantt-Terminplan, KPIs, PDF-Reports und Excel-Import/-Export.

![Tech](https://img.shields.io/badge/Python-3.10%2B-2563EB) ![UI](https://img.shields.io/badge/UI-PySide6%20(Qt6)-10B981) ![DB](https://img.shields.io/badge/DB-SQLite-2563EB)

---

## Überblick

| Baustein | Beschreibung |
|---|---|
| **`server/`** | Zentraler FastAPI-Server mit SQLite-Datenbank. Läuft einmalig auf einem zentralen Rechner/Server im Netzwerk. |
| **`client/`** | Desktop-App (PySide6) für jeden Mitarbeiter-PC. Hält einen lokalen SQLite-Cache und synchronisiert automatisch **beim Start** sowie manuell auf Knopfdruck. |
| **`tests/`** | Headless-Smoke-Test der gesamten Pipeline (Server, Sync, Rechte, KPIs, PDF, Excel). |

### Funktionen
- **Projektübersicht**: Soll/Ist-Fortschritt, Status-Chips, Budget vs. Ist-Kosten vs. Prognose, Terminabweichung, CPI/SPI, Filter nach Status & Projektgröße (Klein/Mittel/Groß),Charts (Balken & Tortendiagramm)
- **Projekt-Detail**: Gantt-Terminplan (Soll/Ist mit Heute-Linie), Meilensteine, Kosten je Kategorie, Stunden/Ressourcen, Projektbericht als PDF
- **Management-Cockpit** (nur sichtbar mit Recht `view_management`): Portfolio-CPI/SPI, Δ-Prognose zum Budget, Problemprojekte-Ranking, vertraulicher Management-Report als PDF
- **Benutzer & Rechte** (nur Admin): Rollen mit 11 granularen Rechten, Benutzer anlegen/sperren, Passwörter zurücksetzen
- **Excel-Import/Export**: Importvorlage, Portfolio-Export (Projekte, Meilensteine, Kosten, Stunden), Import mit Vorschau über Projekt-Code
- **PDF-Reports**: Portfolio-Report, Projektbericht, Management-Report

### Rollen & Rechte (Beispiel-Benutzer)

| Rolle | Sichtbarkeit | Demo-Login |
|---|---|---|
| **admin** | Alles + Benutzerverwaltung | `admin` / `admin` |
| **management** | Alle Projekte + **Management-KPIs** | `geschaeftsfuehrung` / `management123` |
| **projektleiter** | Projekte, Kosten, Stunden, Import/Export (keine Management-KPIs) | `kaltenbrunn` / `projekt123` |
| **mitarbeiter** | Projekte lesend, eigene Stunden erfassen (keine Kosten) | `froster` / `mitarbeit123` |
| **gast** | Nur Projektliste ohne Kosten | `gast` / `gast123` |

---

## Installation

```bash
git clone <repo>
cd projectdash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Server starten (einmalig, zentraler Rechner im Netzwerk)

```bash
python run_server.py          # Standard: http://0.0.0.0:8750
python run_server.py 9000     # eigener Port
```

Die Datenbank (`data/central.db`) wird beim **ersten Start automatisch erzeugt** und direkt mit **10 Beispielprojekten aus der Kältetechnik** (Klein- bis Großprojekt: Supermarkt-Kälteanlage, NH₃/CO₂-Kaskade, Pharmakältezentrale, Retrofit, Wärmepumpe, Brauerei-Prozesskühlung, Rechenzentrums-Abwärme u.v.m.) sowie den Beispiel-Benutzern befüllt. Änderungen der Server-IP: beim Client im Login-Dialog als Server-URL eintragen.

## Client starten (jeder Benutzer-PC)

```bash
python run_client.py
```
Beim ersten Start: **Server-URL**, Benutzer und Passwort im Login-Dialog eingeben. Danach werden die Zugangsdaten gespeichert, und der Client **synchronisiert bei jedem Start** automatisch mit dem zentralen Serverdaten (Delta-Sync über `updated_at`).

## Test

```bash
python tests/test_pipeline.py
```

---

## Architektur

```
┌─────────────────────────┐        HTTP/JSON         ┌──────────────────────────┐
│  Desktop-Client (Qt6)   │ ◄──────────────────────► │  Zentraler Server (FastAPI)│
│  ├─ Login / Token       │   Login, Pull-Sync,      │  ├─ SQLite central.db     │
│  ├─ Lokaler Cache (SQLite) │  Push, Benutzerverw.  │  ├─ Rollen/Rechte-Checks   │
│  ├─ Dashboard/KPIs      │                          │  └─ Seed: 10 Projekte     │
│  ├─ Gantt, PDF, Excel   │                          └──────────────────────────┘
└─────────────────────────┘
```

- **API-Endpoints**: `/login`, `/verify`, `/sync`, `/push`, `/users`, `/users/{id}`, `/password`, `/health`
- **Berechtigungen**: serverseitig erzwungen (403 bei fehlendem Recht), UI blendet Felder zusätzlich aus
- **Offline-Fähigkeit**: Ohne Serververbindung arbeitet der Client aus dem lokalen Cache; Änderungen werden beim nächsten Sync nachgeschoben (aufthalten der Push-Richtlinien beachten: Schreibrechte bleiben serverseitig geprüft).

> Hinweis: Der Server ist für den Einsatz **im internen Netzwerk** gedacht (Fileserver/Intranet-PC). Für einen Internet-Zugriff zusätzlich HTTPS/Terminierung und ggf. IP-Allowlisting vorschalten.
