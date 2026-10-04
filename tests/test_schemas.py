import pytest
from pydantic import ValidationError

from api.app.schemas.parcels import MultiPolygon, Polygon
from api.app.schemas.prediction import Prediction
from api.app.services.mock import MockService


@pytest.fixture
def prediction():
    service = MockService()
    service.load()
    return service.get_prediction("mock-001").model_dump()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("field", ["prediction", "lower", "upper", "interval_level"])
def test_nonfinite_rejected(prediction, field, value):
    prediction[field] = value
    with pytest.raises(ValidationError):
        Prediction(**prediction)


def test_complete_interval(prediction):
    prediction.update(lower=3, upper=4, interval_level=0.9, interval_method="mock-interval")
    assert Prediction(**prediction).lower == 3


@pytest.mark.parametrize("changes", [
    {"lower": 3},
    {"lower": 4, "upper": 5, "interval_level": 0.9, "interval_method": "mock"},
    {"lower": 3, "upper": 4, "interval_level": 1, "interval_method": "mock"},
    {"lower": 3, "upper": 4, "interval_level": 0, "interval_method": "mock"},
])
def test_invalid_intervals(prediction, changes):
    prediction.update(changes)
    with pytest.raises(ValidationError):
        Prediction(**prediction)


def test_multipolygon():
    polygon = [[(-100, 20), (-99, 20), (-99, 21), (-100, 20)]]
    assert MultiPolygon(coordinates=[polygon]).type == "MultiPolygon"


@pytest.mark.parametrize("ring", [
    [(-100, 20), (-99, 20), (-99, 21), (-100, 21)],
    [(-200, 20), (-99, 20), (-99, 21), (-200, 20)],
    [(-100, 20), (-99, 20), (-100, 20)],
])
def test_invalid_geometry(ring):
    with pytest.raises(ValidationError):
        Polygon(coordinates=[ring])
