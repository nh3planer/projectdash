import requests


class ApiError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class Api:
    def __init__(self, base_url, token=None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _post(self, path, payload, auth=True):
        try:
            r = requests.post(f"{self.base_url}{path}", json=payload,
                              headers=self._headers() if auth else {}, timeout=15)
        except requests.RequestException as e:
            raise ApiError(f"Server nicht erreichbar: {e}")
        if r.status_code in (401, 403):
            detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
            raise ApiError(detail, status=r.status_code)
        if r.status_code >= 400:
            raise ApiError(f"Serverfehler {r.status_code}: {r.text}")
        return r.json()

    def login(self, username, password):
        data = self._post("/login", {"username": username, "password": password}, auth=False)
        self.token = data["token"]
        return data

    def verify(self):
        return self._post("/verify", {})

    def sync(self, since):
        return self._post("/sync", {"since": since})

    def push(self, table, rows):
        return self._post("/push", {"table": table, "rows": rows})

    def users(self):
        r = requests.get(f"{self.base_url}/users", headers=self._headers(), timeout=15)
        if r.status_code >= 400:
            raise ApiError(r.text, status=r.status_code)
        return r.json()

    def create_user(self, payload):
        r = requests.post(f"{self.base_url}/users", json=payload, headers=self._headers(), timeout=15)
        if r.status_code >= 400:
            raise ApiError(r.json().get("detail", r.text), status=r.status_code)
        return r.json()

    def update_user(self, user_id, payload):
        r = requests.post(f"{self.base_url}/users/{user_id}", json=payload, headers=self._headers(), timeout=15)
        if r.status_code >= 400:
            raise ApiError(r.json().get("detail", r.text), status=r.status_code)
        return r.json()

    def change_password(self, old_password, new_password):
        return self._post("/password", {"old_password": old_password, "new_password": new_password})
