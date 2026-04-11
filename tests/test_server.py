# Copyright (c) Meta Platforms, Inc. and affiliates.

from fastapi.testclient import TestClient

try:
    from hoja.server.app import app
except ImportError:
    from server.app import app

client = TestClient(app)


def test_schema_endpoint():
    response = client.get("/schema")
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert "observation" in data
    assert "state" in data


def test_dashboard_endpoint():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
