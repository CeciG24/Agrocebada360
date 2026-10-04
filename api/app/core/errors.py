import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from api.app.schemas.common import ErrorBody, ErrorCode, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, status_code: int, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    status: int, code: ErrorCode, message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or []))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError) -> JSONResponse:
        logger.warning("Respuesta de servicio: %s", exc.code)
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            ErrorDetail(
                field=".".join(str(part) for part in error["loc"]),
                message="Valor inválido para este parámetro.",
            ) for error in exc.errors()
        ]
        return error_response(422, "VALIDATION_ERROR", "Parámetros inválidos.", details)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        mapping: dict[int, tuple[ErrorCode, str]] = {
            404: ("ROUTE_NOT_FOUND", "No se encontró la ruta solicitada."),
            422: ("VALIDATION_ERROR", "Parámetros inválidos."),
            503: ("DATA_UNAVAILABLE", "El servicio no está disponible."),
            500: ("INTERNAL_ERROR", "Ocurrió un error interno."),
        }
        if exc.status_code in mapping:
            code, message = mapping[exc.status_code]
            return error_response(exc.status_code, code, message)
        # Otros estados HTTP (por ejemplo 405) no están definidos en v0.1.0.
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Error interno atendiendo solicitud", exc_info=exc)
        return error_response(500, "INTERNAL_ERROR", "Ocurrió un error interno.")
