from typing import Annotated, Self

from pydantic import Field, FiniteFloat, model_validator

from api.app.schemas.common import ContractModel, Meta
from api.app.schemas.parcels import NonBlank


class Prediction(ContractModel):
    parcel_id: NonBlank
    prediction: FiniteFloat
    unit: NonBlank
    lower: FiniteFloat | None
    upper: FiniteFloat | None
    interval_level: Annotated[FiniteFloat, Field(gt=0, lt=1)] | None
    interval_method: NonBlank | None
    model_version: NonBlank
    meta: Meta

    @model_validator(mode="after")
    def coherent_interval(self) -> Self:
        values = (self.lower, self.upper, self.interval_level, self.interval_method)
        if all(value is None for value in values):
            return self
        if any(value is None for value in values):
            raise ValueError("El intervalo debe estar completo o ser null")
        if not self.lower <= self.prediction <= self.upper:
            raise ValueError("El intervalo debe contener la predicción")
        return self
