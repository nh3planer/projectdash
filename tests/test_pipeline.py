import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _wait_for_server(api, timeout=20):
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(f"{api}/health", timeout=2).raise_for_status()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def run():
    port = 8788
    base = f"http://127.0.0.1:{port}"
    tmp = tempfile.mkdtemp(prefix="projectdash_test_")
    db_path = os.path.join(tmp, "central.db")
    env = dict(os.environ, PROJECTDASH_DB=db_path, PYTHONPATH=ROOT)
    server = subprocess.Popen([sys.executable, os.path.join(ROOT, "run_server.py"), str(port)],
                              env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert _wait_for_server(base), "Server ist nicht gestartet"
    try:
        from client.api import Api, ApiError
        from client.localdb import LocalDB
        from client.kpi import PortfolioKPI
        from client import excel_io, pdf_report

        api = Api(base)
        admin = api.login("admin", "admin")
        assert admin["permissions"] and "manage_users" in admin["permissions"]

        guest = Api(base)
        guest.login("gast", "gast123")
        try:
            guest.push("projects", [{"id": 1, "budget": 1}])
            raise AssertionError("Gast darf keine Projekte ändern")
        except ApiError:
            pass

        sync = api.sync("")
        assert len(sync["data"]["projects"]) == 10, "Seed muss 10 Projekte enthalten"
        assert all("password_hash" not in u for u in sync["data"]["users"])

        db = LocalDB(os.path.join(tmp, "cache.db"))
        db.full_sync(sync)
        assert len(db.projects()) == 10
        assert len(db.phases(db.projects()[0]["id"])) == 6

        costs, hours = {}, {}
        for c in db.rows("cost_entries"):
            costs.setdefault(c["project_id"], []).append(c)
        for h in db.rows("hours_entries"):
            hours.setdefault(h["project_id"], []).append(h)
        pf = PortfolioKPI(db.projects(), costs, hours)
        assert pf.portfolio_cpi > 0 and pf.total_budget > 17_000_000

        pushed = api.push("cost_entries", [{"project_id": db.projects()[0]["id"], "date": "2026-11-01",
                                            "category": "Test", "amount_plan": 100, "amount_actual": 50}])
        assert pushed["accepted_ids"]

        pdf_report.portfolio_report(os.path.join(tmp, "portfolio.pdf"), pf)
        assert os.path.getsize(os.path.join(tmp, "portfolio.pdf")) > 1000
        pdf_report.management_report(os.path.join(tmp, "management.pdf"), pf)
        pdf_report.project_report(os.path.join(tmp, "project.pdf"), pf.items[0],
                                  db.phases(pf.items[0].project["id"]),
                                  db.milestones(pf.items[0].project["id"]),
                                  db.costs(pf.items[0].project["id"]),
                                  db.hours(pf.items[0].project["id"]))

        xlsx = os.path.join(tmp, "export.xlsx")
        excel_io.export_workbook([
            ("Projekte", excel_io.PROJECT_FIELDS_EXPORT, db.projects()),
        ]).save(xlsx)
        imported = excel_io.import_workbook(xlsx)
        assert len(imported["projects"]) == 10
        assert imported["projects"][0]["code"].startswith("K-10")
        print(json.dumps({"status": "ok", "projects": 10, "port": port}, ensure_ascii=False))
        return 0
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(run())
