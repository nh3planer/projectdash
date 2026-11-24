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

## Schnelltest ohne Installation (2 Minuten)

Auf einem Rechner (im Netzwerk der späteren Benutzer):

```bash
pip install -r requirements.txt
python run_server.py        # Terminal 1: zentraler Server, Port 8750
python run_client.py       # Terminal 2: Desktop-Oberfläche
```

Im Login-Dialog des Clients als Server `http://<Adresse des Server-PCs>:8750` eintragen – auf demselben Rechner `http://localhost:8750`. Dann nacheinander mit den Demo-Benutzern (siehe Tabelle unten) einloggen und die unterschiedlichen Rechte ausprobieren:

- `admin` / `admin` – alles inkl. Benutzerverwaltung (Seite „Benutzer & Rechte")
- `geschaeftsfuehrung` / `management123` – zusätzlich das Management-Cockpit mit den vertraulichen KPIs
- `kaltenbrunn` / `projekt123` – Projektleitung: Projekte bearbeiten, Kosten, Import/Export – **ohne** Management-Cockpit
- `froster` / `mitarbeit123` – Mitarbeiter: kostenfreie Ansicht, Management und Kosten bleiben verborgen
- `gast` / `gast123` – nur Projektliste

Doppelklick auf eine Projektzeile öffnet das Projektdetail (Gantt, Meilensteine, Kosten, Stunden, PDF-Report).

> Wichtig für den produktiven Betrieb: beim ersten Login die Standard-Passwörter über „Passwort ändern“ ersetzen bzw. als Admin neue Benutzer anlegen.

## Windows-Exe / Installer erstellen

Windows-Exe-Dateien müssen auf einem **Windows-Rechner** gebaut werden (einmalig, ca. 5 Minuten):

1. Dieses Repository auf einem Windows-PC klonen/herunterladen
2. `build\build_windows.bat` **doppelklicken** – erzeugt im Ordner `dist`:
   - `ProjectDashServer.exe` (einmalig auf dem zentralen Server-PC, Port 8750)
   - `ProjectDashClient.exe` (auf jeden Mitarbeiter-PC kopieren, kein Python nötig)
3. Optional ein echtes Setup-Programm bauen: [Inno Setup 6](https://jrsoftware.org/isinfo.php) installieren und `build\installer.iss` kompilieren → ergibt `Setup\ProjectDashSetup.exe` mit Startmenü-Einträgen und Desktop-Symbol

Die Server-Datenbank `data\central.db` wird beim ersten Start **neben der Exe** angelegt und automatisch mit den 10 Beispielprojekten befüllt. Server-Port lässt sich über die Umgebungsvariable `PROJECTDASH_PORT` ändern, der Datenbankpfad über `PROJECTDASH_DB`.

> Sicherheitshinweis: Der Server ist für das interne Netzwerk gedacht. Beim ersten produktiven Einsatz die Demo-Benutzer prüfen/deaktivieren (als Admin unter „Benutzer & Rechte“) und den Server nicht ohne zusätzliche Absicherung (VPN/HTTPS-Reverse-Proxy) aus dem Internet erreichbar machen.

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
