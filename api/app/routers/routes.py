from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from api.app.schemas.common import ErrorResponse, Health
from api.app.schemas.parcels import ParcelDetail, ParcelList, ParcelMapList
from api.app.schemas.prediction import Prediction
from api.app.services.base import ParcelService

router = APIRouter()
ERRORS = {status: {"model": ErrorResponse} for status in (404, 422, 503, 500)}


def get_service(request: Request) -> ParcelService:
    return request.app.state.service


Service = Annotated[ParcelService, Depends(get_service)]
ParcelID = Annotated[str, Path(min_length=1, pattern=r"\S")]


@router.get("/health", response_model=Health, responses={503: {"model": Health}, 500: {"model": ErrorResponse}})
def health(request: Request, response: Response, service: Service) -> Health:
    ready = service.data_ready and (request.app.state.settings.mode == "mock" or service.model_loaded)
    response.status_code = 200 if ready else 503
    return Health(status="ok" if ready else "degraded", mode=request.app.state.settings.mode,
                  model_loaded=service.model_loaded, data_ready=service.data_ready)


@router.get("/parcels", response_model=ParcelList | ParcelMapList,
            responses={status: ERRORS[status] for status in (422, 503, 500)})
def parcels(
    service: Service,
    region: Annotated[str | None, Query(min_length=1, pattern=r"\S")] = None,
    include_geometry: bool = False,
) -> ParcelList | ParcelMapList:
    return service.list_parcels(region, include_geometry)


@router.get("/parcel/{id}", response_model=ParcelDetail, responses=ERRORS)
def parcel(id: ParcelID, service: Service) -> ParcelDetail:
    return service.get_parcel(id)


@router.get("/predict/{id}", response_model=Prediction, responses=ERRORS)
def predict(id: ParcelID, service: Service) -> Prediction:
    return service.get_prediction(id)
