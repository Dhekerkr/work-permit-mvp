import os
os.environ["DATABASE_URL"] = "sqlite:///./test_work_permits.db"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app
from seed import seed

def login(client, identifier):
    r = client.post("/api/auth/login", json={"identifier": identifier, "password": "Demo123!"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_end_to_end_and_permissions():
    Base.metadata.drop_all(engine); seed()
    with TestClient(app) as client:
        prod, hse = login(client, "PROD001"), login(client, "HSE001")
        body = {"site":"AGIL Gaz Radès","work_location":"Zone test","contractor":"Test Maintenance","responsible_person":"Responsable test","work_description":"Soudage contrôlé","work_types":["WELDING"],"safety_checks":[{"code":f"S{i}","checked":True} for i in range(1,10)],"gas_measurement":{"applicable":True,"o2":20.8,"lel":0},"hot_work_checks":[{"code":f"H{i}","checked":True} for i in range(1,7)],"planned_start_at":"2026-09-18T08:00:00Z","expires_at":"2026-09-18T17:00:00Z"}
        created = client.post("/api/permits", json=body, headers=prod)
        assert created.status_code == 200
        pid = created.json()["id"]
        assert client.post(f"/api/permits/{pid}/submit", headers=prod).json()["status"] == "PENDING_APPROVAL"
        assert client.post(f"/api/permits/{pid}/approve", headers=prod).status_code == 403
        active = client.post(f"/api/permits/{pid}/approve", headers=hse)
        assert active.json()["status"] == "ACTIVE"
        suspended = client.post(f"/api/permits/{pid}/suspend", json={"comment":"Arrêt de contrôle"}, headers=hse)
        assert suspended.json()["status"] == "SUSPENDED"
        assert client.post(f"/api/permits/{pid}/resume", headers=hse).json()["status"] == "ACTIVE"
        checks = [{"code":f"C{i}","checked":True} for i in range(1,6)]
        assert client.post(f"/api/permits/{pid}/complete", json={"checks":checks}, headers=prod).json()["status"] == "COMPLETED"
        closed = client.post(f"/api/permits/{pid}/close", headers=hse)
        assert closed.json()["status"] == "CLOSED"
        assert len(closed.json()["audit_logs"]) >= 7

