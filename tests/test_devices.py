from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def _register_and_login(email: str = "dev@example.com", password: str = "pass"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"], data["refresh_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_list_and_revoke_device():
    access, _ = _register_and_login("deviceuser@example.com")
    # List devices
    r = client.get("/api/v1/auth/devices", headers=_auth_header(access))
    assert r.status_code == 200, r.text
    devices = r.json()
    assert isinstance(devices, list)
    assert len(devices) >= 1
    device_id = devices[0]["id"]

    # Revoke this device
    r = client.delete(f"/api/v1/auth/devices/{device_id}", headers=_auth_header(access))
    assert r.status_code == 204, r.text

    # It should disappear from the list
    r = client.get("/api/v1/auth/devices", headers=_auth_header(access))
    assert r.status_code == 200
    ids = [d["id"] for d in r.json()]
    assert device_id not in ids
