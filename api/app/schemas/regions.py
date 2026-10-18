from typing import Annotated, Self

from pydantic import Field, FiniteFloat, StrictInt, model_validator

from api.app.schemas.common import ContractModel, Meta
from api.app.schemas.parcels import NonBlank


class RegionSummary(ContractModel):
    region: NonBlank
    parcel_count: Annotated[StrictInt, Field(ge=1)]
    predicted_count: Annotated[StrictInt, Field(ge=0)]
    mean_prediction: FiniteFloat | None
    unit: NonBlank | None
    model_version: NonBlank | None
    meta: Meta

    @model_validator(mode='after')
    def coherent_coverage(self) -> Self:
        if self.predicted_count > self.parcel_count:
            raise ValueError('La cobertura no puede superar el catálogo regional.')
        context = [self.mean_prediction, self.unit, self.model_version]
        if self.predicted_count == 0:
            if any(value is not None for value in context):
                raise ValueError('Sin predicciones: media, unidad y modelo deben ser null.')
        elif any(value is None for value in context) or (self.meta.mode == 'real' and self.unit != 't/ha'):
            raise ValueError('El resumen requiere media, modelo y unidad compatible.')
        return self
