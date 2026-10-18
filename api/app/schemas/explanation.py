import math
from typing import Literal, Self

from pydantic import FiniteFloat, model_validator

from api.app.schemas.common import ContractModel, Meta
from api.app.schemas.parcels import NonBlank

RECONSTRUCTION_ATOL = 1e-8


class FeatureImpact(ContractModel):
    feature: NonBlank
    friendly_name: NonBlank
    impact: FiniteFloat
    direction: Literal['positive', 'negative', 'neutral']

    @model_validator(mode='after')
    def consistent_sign(self) -> Self:
        expected = 'positive' if self.impact > 0 else 'negative' if self.impact < 0 else 'neutral'
        if self.direction != expected:
            raise ValueError('La dirección debe corresponder al signo del impacto.')
        return self


class Explanation(ContractModel):
    parcel_id: NonBlank
    status: Literal['available', 'unavailable']
    reason: Literal['EXPLANATION_NOT_READY'] | None
    method: Literal['shap'] | None
    model_version: NonBlank | None
    output_space: NonBlank | None
    base_value: FiniteFloat | None
    explained_output: FiniteFloat | None
    features: list[FeatureImpact]
    meta: Meta

    @model_validator(mode='after')
    def coherent_explanation(self) -> Self:
        context = [self.method, self.model_version, self.output_space, self.base_value, self.explained_output]
        if self.status == 'unavailable':
            if self.reason != 'EXPLANATION_NOT_READY' or self.features or any(v is not None for v in context):
                raise ValueError('Una explicación no disponible debe tener contexto null y features vacías.')
            return self
        if self.reason is not None or any(v is None for v in context) or not self.features:
            raise ValueError('La explicación disponible requiere todo su contexto y contribuciones.')
        names = [item.feature for item in self.features]
        if len(names) != len(set(names)):
            raise ValueError('Las contribuciones deben ser únicas por feature.')
        if self.features != sorted(self.features, key=lambda item: (-abs(item.impact), item.feature)):
            raise ValueError('Las contribuciones deben ordenarse por impacto absoluto y feature.')
        reconstructed = self.base_value + math.fsum(item.impact for item in self.features)
        if not math.isclose(reconstructed, self.explained_output, rel_tol=0, abs_tol=RECONSTRUCTION_ATOL):
            raise ValueError('Las contribuciones no reconstruyen la salida explicada.')
        return self


def unavailable_explanation(parcel_id, mode):
    return Explanation(parcel_id=parcel_id, status='unavailable', reason='EXPLANATION_NOT_READY',
                       method=None, model_version=None, output_space=None, base_value=None,
                       explained_output=None, features=[], meta=Meta(mode=mode))
