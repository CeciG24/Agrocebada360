import pytest
from fastapi.testclient import TestClient

from api.app.main import create_app
from api.app.services.mock import MockService


@pytest.fixture
def client():
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        yield client


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["code"] == code
    return body["error"]


def test_only_requested_routes(client):
    assert {route.path for route in client.app.routes} == {
        "/health", "/parcels", "/parcel/{id}", "/predict/{id}",
    }


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", "mode": "mock", "contract_version": "0.1.0",
        "model_loaded": False, "data_ready": True,
    }


def test_map_in_one_request(client, monkeypatch):
    def forbidden(*args):
        raise AssertionError("El listado no debe consultar el detalle")
    monkeypatch.setattr(client.app.state.service, "get_parcel", forbidden)
    base = client.get("/parcels").json()
    assert base == client.get("/parcels?include_geometry=false").json()
    mapped = client.get("/parcels?include_geometry=true").json()
    assert set(base) == {"items", "total", "meta"}
    assert base["total"] == mapped["total"] == 197
    assert len(mapped["items"]) == 197
    ids = [item["id"] for item in base["items"]]
    assert ids == sorted(set(ids))
    assert ids[0] == "mock-001"
    for simple, full in zip(base["items"], mapped["items"]):
        assert set(simple) == {"id", "region"}
        assert set(full) == {"id", "region", "geometry"}
        assert simple == {k: full[k] for k in simple}
        assert full["geometry"]["type"] == "Polygon"
        ring = full["geometry"]["coordinates"][0]
        assert ring[0] == ring[-1]
    assert base["meta"] == mapped["meta"] == {
        "contract_version": "0.1.0", "mode": "mock",
        "cycle": "2025-04/2025-10", "data_cutoff": "2025-10-31",
    }


@pytest.mark.parametrize("geometry", ["true", "false"])
def test_region_filter(client, geometry):
    body = client.get("/parcels", params={"region": "mock-region-1", "include_geometry": geometry}).json()
    assert body["total"] == len(body["items"]) == 99
    assert all(p["region"] == "mock-region-1" for p in body["items"])
    assert all(("geometry" in p) == (geometry == "true") for p in body["items"])
    empty = client.get("/parcels", params={"region": "unknown", "include_geometry": geometry})
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total"] == 0


def test_detail_matches_map_and_missing_geometry(client):
    mapped = client.get("/parcels?include_geometry=true").json()["items"][0]
    detail = client.get("/parcel/mock-001").json()
    assert set(detail) == {"id", "region", "geometry", "meta"}
    assert {k: detail[k] for k in mapped} == mapped
    client.app.state.service.parcels["mock-001"].geometry = None
    mapped = client.get("/parcels?include_geometry=true").json()
    assert mapped["total"] == 197
    assert mapped["items"][0]["geometry"] is None
    assert client.get("/parcel/mock-001").json()["geometry"] is None


def test_prediction(client):
    response = client.get("/predict/mock-001")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"parcel_id", "prediction", "unit", "lower", "upper",
                         "interval_level", "interval_method", "model_version", "meta"}
    assert body["prediction"] == 3.2
    assert body["unit"] == "mock_unit"
    assert body["model_version"] == "mock-v1"
    assert body["meta"]["mode"] == "mock"
    assert all(body[k] is None for k in ("lower", "upper", "interval_level", "interval_method"))
    assert client.get("/predict/mock-001").json() == body


@pytest.mark.parametrize("path", ["/parcel/unknown", "/predict/unknown"])
def test_unknown_parcel(client, path):
    assert_error(client.get(path), 404, "PARCEL_NOT_FOUND")


@pytest.mark.parametrize("path", ["/unknown", "/explain/mock-001", "/docs"])
def test_unknown_route(client, path):
    assert_error(client.get(path), 404, "ROUTE_NOT_FOUND")


@pytest.mark.parametrize("path", [
    "/parcels?include_geometry=invalid", "/parcels?region=", "/parcels?region=%20",
    "/parcel/%20", "/predict/%20",
])
def test_invalid_parameters(client, path):
    error = assert_error(client.get(path), 422, "VALIDATION_ERROR")
    assert error["details"]
    assert all(set(d) == {"field", "message"} for d in error["details"])


def test_unavailable_prediction(client):
    del client.app.state.service.predictions["mock-001"]
    assert_error(client.get("/predict/mock-001"), 503, "PREDICTION_UNAVAILABLE")


def test_unavailable_catalog(client):
    client.app.state.service.data_ready = False
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["data_ready"] is False
    for path in ("/parcels", "/parcels?include_geometry=true", "/parcel/mock-001", "/predict/mock-001"):
        assert_error(client.get(path), 503, "DATA_UNAVAILABLE")


def test_startup_failure(monkeypatch):
    def fail(self):
        raise RuntimeError("internal startup detail")
    monkeypatch.setattr(MockService, "load", fail)
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        assert client.get("/health").status_code == 503
        assert_error(client.get("/parcels"), 503, "DATA_UNAVAILABLE")


def test_unexpected_error_is_safe(client, monkeypatch, caplog):
    def fail(*args):
        raise RuntimeError("private-server-path")
    monkeypatch.setattr(client.app.state.service, "get_prediction", fail)
    response = client.get("/predict/mock-001")
    assert_error(response, 500, "INTERNAL_ERROR")
    assert "private-server-path" not in response.text
    assert "private-server-path" in caplog.text


def test_loaded_once_per_lifespan(monkeypatch):
    original = MockService.load
    calls = []
    def counted(self):
        calls.append(self)
        original(self)
    monkeypatch.setattr(MockService, "load", counted)
    with TestClient(create_app()) as client:
        for _ in range(3):
            assert client.get("/predict/mock-001").status_code == 200
        assert len(calls) == 1
