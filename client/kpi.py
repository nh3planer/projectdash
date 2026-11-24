from datetime import date, datetime

EUR = " €"


def fmt_eur(v, compact=False):
    if v is None:
        v = 0
    if compact:
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.2f} Mio €"
        if abs(v) >= 1000:
            return f"{v/1000:.1f} T€"
    return f"{v:,.0f}{EUR}".replace(",", ".")


def fmt_pct(v):
    return f"{(v or 0)*100:.0f} %"


def parse_date(s):
    if not s:
        return None
    if isinstance(s, date):
        return s
    return datetime.fromisoformat(str(s)[:10]).date()


def days_between(a, b):
    if not a or not b:
        return 0
    return (parse_date(b) - parse_date(a)).days


class ProjectKPI:
    def __init__(self, project, costs=None, hours=None):
        p = project
        self.project = p
        self.budget = p.get("budget") or 0
        self.p_plan = p.get("progress_plan") or 0
        self.p_act = p.get("progress_actual") or 0
        self.start = parse_date(p.get("start_plan"))
        self.end_plan = parse_date(p.get("end_plan"))
        self.forecast = parse_date(p.get("end_forecast")) or self.end_plan

        if costs is not None:
            self.cost_plan = sum(c.get("amount_plan") or 0 for c in costs)
            self.cost_actual = sum(c.get("amount_actual") or 0 for c in costs)
        else:
            self.cost_plan = self.budget
            self.cost_actual = p.get("cost_actual") or 0
        if hours is not None:
            self.hours_plan = sum(h.get("hours_plan") or 0 for h in hours)
            self.hours_actual = sum(h.get("hours_actual") or 0 for h in hours)
        else:
            self.hours_plan = 0
            self.hours_actual = 0

        self.ev = self.budget * self.p_act
        self.pv = self.budget * self.p_plan
        self.cpi = (self.ev / self.cost_actual) if self.cost_actual > 0 else 1.0
        self.spi = (self.ev / self.pv) if self.pv > 0 else (1.0 if self.p_act == 0 else 1.0)
        self.cv = self.ev - self.cost_actual
        self.sv = self.ev - self.pv
        self.eac = self.budget / self.cpi if self.cpi > 0 else self.budget
        self.vac = self.budget - self.eac
        self.date_variance = days_between(self.end_plan, self.forecast)
        self.today = date.today()
        self.total_days = days_between(self.start, self.end_plan) or 1
        self.elapsed = max(0, min(1, (days_between(self.start, self.today) / self.total_days)))

    @property
    def status_key(self):
        s = self.project.get("status", "")
        return {
            "geplant": "geplant", "laufend": "laufend",
            "kritisch": "kritisch", "abgeschlossen": "abgeschlossen",
        }.get(s, s)

    @property
    def cost_pct(self):
        return (self.cost_actual / self.budget) if self.budget > 0 else 0

    def to_dict(self):
        return {
            "budget": self.budget, "plan_bis_heute": self.pv, "ist_kosten": self.cost_actual,
            "ev": self.ev, "cpi": self.cpi, "spi": self.spi,
            "forecast_end": self.eac, "delta_budget": self.vac,
            "termin_delta": self.date_variance,
            "p_plan": self.p_plan, "p_act": self.p_act,
            "hours_plan": self.hours_plan, "hours_actual": self.hours_actual,
        }


class PortfolioKPI:
    def __init__(self, projects, costs_by_pid, hours_by_pid):
        self.items = []
        for p in projects:
            costs = costs_by_pid.get(p["id"])
            hours = hours_by_pid.get(p["id"])
            if costs is None:
                costs = [
                    {"amount_plan": p.get("budget") or 0, "amount_actual": p.get("budget") * (p.get("progress_actual") or 0)},
                ]
            self.items.append(ProjectKPI(p, costs, hours))
        if not self.items:
            self.items = [ProjectKPI({"budget": 0, "progress_plan": 0, "progress_actual": 0,
                                      "start_plan": None, "end_plan": None}, [], [])]
        self.count = len(projects)
        self.running = sum(1 for p in projects if p.get("status") == "laufend")
        self.critical = sum(1 for p in projects if p.get("status") == "kritisch")
        self.done = sum(1 for p in projects if p.get("status") == "abgeschlossen")
        self.planned = sum(1 for p in projects if p.get("status") == "geplant")
        self.total_budget = sum(i.budget for i in self.items)
        self.total_plan_now = sum(i.pv for i in self.items)
        self.total_actual = sum(i.cost_actual for i in self.items)
        self.total_ev = sum(i.ev for i in self.items)
        self.total_forecast = sum(i.eac for i in self.items)
        self.total_hours_plan = sum(i.hours_plan for i in self.items)
        self.total_hours_actual = sum(i.hours_actual for i in self.items)
        self.cost_delta = self.total_actual - self.total_plan_now
        self.forecast_delta = self.total_forecast - self.total_budget
        self.portfolio_cpi = (self.total_ev / self.total_actual) if self.total_actual else 1.0
        self.portfolio_spi = (self.total_ev / self.total_plan_now) if self.total_plan_now else 1.0
        self.on_time = [i for i in self.items if i.date_variance <= 0 and i.project.get("status") != "abgeschlossen"]

    def worst_projects(self, n=5):
        return sorted(self.items, key=lambda i: (i.cpi - 1) + (i.spi - 1))[:n]

    def best_projects(self, n=5):
        return sorted(self.items, key=lambda i: (i.cpi - 1) + (i.spi - 1), reverse=True)[:n]
