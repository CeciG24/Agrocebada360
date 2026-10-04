from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from api.app.schemas.common import ContractModel, Meta

NonBlank = Annotated[str, Field(min_length=1, pattern=r"\S")]
Position = tuple[
    Annotated[float, Field(ge=-180, le=180)],
    Annotated[float, Field(ge=-90, le=90)],
]
Ring = Annotated[list[Position], Field(min_length=4)]
PolygonCoordinates = Annotated[list[Ring], Field(min_length=1)]


class Polygon(ContractModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: PolygonCoordinates

    @model_validator(mode="after")
    def closed_rings(self) -> Self:
        if any(ring[0] != ring[-1] for ring in self.coordinates):
            raise ValueError("Los anillos deben estar cerrados")
        return self


class MultiPolygon(ContractModel):
    type: Literal["MultiPolygon"] = "MultiPolygon"
    coordinates: Annotated[list[PolygonCoordinates], Field(min_length=1)]

    @model_validator(mode="after")
    def closed_rings(self) -> Self:
        for coordinates in self.coordinates:
            Polygon(coordinates=coordinates)
        return self


Geometry = Annotated[Polygon | MultiPolygon, Field(discriminator="type")]


class ParcelSummary(ContractModel):
    id: NonBlank
    region: NonBlank | None


class ParcelMapItem(ParcelSummary):
    geometry: Geometry | None


class ParcelDetail(ParcelMapItem):
    meta: Meta


class ParcelList(ContractModel):
    items: list[ParcelSummary]
    total: Annotated[int, Field(ge=0)]
    meta: Meta

    @model_validator(mode="after")
    def matching_total(self) -> Self:
        if self.total != len(self.items):
            raise ValueError("total debe coincidir con items")
        return self


class ParcelMapList(ContractModel):
    items: list[ParcelMapItem]
    total: Annotated[int, Field(ge=0)]
    meta: Meta

    @model_validator(mode="after")
    def matching_total(self) -> Self:
        if self.total != len(self.items):
            raise ValueError("total debe coincidir con items")
        return self
