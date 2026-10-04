from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Meta(ContractModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    mode: Literal["mock", "real"]
    cycle: Literal["2025-04/2025-10"] = "2025-04/2025-10"
    data_cutoff: Literal["2025-10-31"] = "2025-10-31"


class Health(ContractModel):
    status: Literal["ok", "degraded"]
    mode: Literal["mock", "real"]
    contract_version: Literal["0.1.0"] = "0.1.0"
    model_loaded: bool
    data_ready: bool


ErrorCode = Literal[
    "PARCEL_NOT_FOUND", "REGION_NOT_FOUND", "ROUTE_NOT_FOUND",
    "VALIDATION_ERROR", "DATA_UNAVAILABLE", "MODEL_UNAVAILABLE",
    "PREDICTION_UNAVAILABLE", "EXPLANATION_UNAVAILABLE", "RISK_UNAVAILABLE",
    "REGION_DATA_UNAVAILABLE", "REGION_SUMMARY_UNAVAILABLE", "INTERNAL_ERROR",
]


class ErrorDetail(ContractModel):
    field: str
    message: str


class ErrorBody(ContractModel):
    code: ErrorCode
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(ContractModel):
    error: ErrorBody
