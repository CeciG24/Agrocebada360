from typing import Literal, Self

from pydantic import model_validator

from api.app.schemas.common import ContractModel, Meta
from api.app.schemas.parcels import NonBlank


class Risk(ContractModel):
    parcel_id: NonBlank
    status: Literal['available', 'unavailable']
    reason: Literal['RISK_NOT_READY'] | None
    level: Literal['low', 'medium', 'high'] | None
    method_version: NonBlank | None
    model_version: NonBlank | None
    description: NonBlank | None
    meta: Meta

    @model_validator(mode='after')
    def consistent_availability(self) -> Self:
        context = [self.level, self.method_version, self.model_version, self.description]
        if self.status == 'unavailable':
            if self.reason != 'RISK_NOT_READY' or any(value is not None for value in context):
                raise ValueError('Riesgo no disponible requiere contexto null y RISK_NOT_READY.')
        elif self.reason is not None or any(value is None for value in context):
            raise ValueError('Una evaluación disponible requiere nivel, metodología, modelo y descripción.')
        return self


def unavailable_risk(parcel_id, mode):
    return Risk(parcel_id=parcel_id, status='unavailable', reason='RISK_NOT_READY',
                level=None, method_version=None, model_version=None, description=None, meta=Meta(mode=mode))
