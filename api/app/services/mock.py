"""Fixtures sintéticas deterministas. No usa el dataset ni realiza inferencia."""

from api.app.core.errors import ServiceError
from api.app.schemas.common import Meta
from api.app.schemas.parcels import (
    ParcelDetail, ParcelList, ParcelMapItem, ParcelMapList, ParcelSummary, Polygon,
)
from api.app.schemas.prediction import Prediction
from api.app.schemas.explanation import unavailable_explanation
from api.app.schemas.risk import unavailable_risk
from api.app.schemas.regions import RegionSummary


class MockService:
    @property
    def model_loaded(self) -> bool:
        return False

    def __init__(self) -> None:
        self.parcels: dict[str, ParcelMapItem] = {}
        self.predictions: dict[str, Prediction] = {}
        self.data_ready = False
        self.regions = {}

    def load(self) -> None:
        for index in range(197):
            parcel_id = f"mock-{index + 1:03d}"
            longitude = round(-100 + (index % 20) * 0.002, 6)
            latitude = round(20 + (index // 20) * 0.002, 6)
            east, north = round(longitude + 0.001, 6), round(latitude + 0.001, 6)
            geometry = Polygon(coordinates=[[
                (longitude, latitude), (east, latitude), (east, north),
                (longitude, north), (longitude, latitude),
            ]])
            self.parcels[parcel_id] = ParcelMapItem(
                id=parcel_id, region=f"mock-region-{index % 2 + 1}", geometry=geometry,
            )
            self.predictions[parcel_id] = Prediction(
                parcel_id=parcel_id, prediction=round(3.2 + (index % 10) * 0.1, 2),
                unit="mock_unit", lower=None, upper=None, interval_level=None,
                interval_method=None, model_version="mock-v1", meta=Meta(mode="mock"),
            )
        from api.app.services.region_summary import summarize_regions
        self.regions = summarize_regions(self.parcels, self.predictions, 'mock')
        self.data_ready = True

    def require_data(self) -> None:
        if not self.data_ready:
            raise ServiceError(503, "DATA_UNAVAILABLE", "El catálogo no está disponible.")

    def list_parcels(self, region: str | None, include_geometry: bool) -> ParcelList | ParcelMapList:
        self.require_data()
        items = [p for p in sorted(self.parcels.values(), key=lambda p: p.id)
                 if region is None or p.region == region]
        if include_geometry:
            return ParcelMapList(items=items, total=len(items), meta=Meta(mode="mock"))
        return ParcelList(
            items=[ParcelSummary(id=p.id, region=p.region) for p in items],
            total=len(items), meta=Meta(mode="mock"),
        )

    def get_parcel(self, parcel_id: str) -> ParcelDetail:
        self.require_data()
        parcel = self.parcels.get(parcel_id)
        if parcel is None:
            raise ServiceError(404, "PARCEL_NOT_FOUND", "No se encontró la parcela solicitada.")
        return ParcelDetail(**parcel.model_dump(), meta=Meta(mode="mock"))

    def get_prediction(self, parcel_id: str) -> Prediction:
        self.get_parcel(parcel_id)
        prediction = self.predictions.get(parcel_id)
        if prediction is None:
            raise ServiceError(503, "PREDICTION_UNAVAILABLE", "La predicción no está disponible.")
        return prediction

    def get_explanation(self, parcel_id: str):
        self.get_parcel(parcel_id)
        return unavailable_explanation(parcel_id, 'mock')

    def get_risk(self, parcel_id: str):
        self.get_parcel(parcel_id)
        return unavailable_risk(parcel_id, 'mock')

    def get_region(self, region: str) -> RegionSummary:
        self.require_data()
        if region not in self.regions:
            raise ServiceError(404, 'REGION_NOT_FOUND', 'No se encontró la región solicitada.')
        return self.regions[region]
