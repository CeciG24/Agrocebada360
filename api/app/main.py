import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from api.app.core.config import Settings, get_settings
from api.app.core.errors import register_error_handlers
from api.app.routers.routes import router
from api.app.services.mock import MockService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logging.basicConfig(level=config.log_level)
        service = MockService()
        app.state.service = service
        try:
            service.load()
            logger.info("Catálogo MOCK inicializado: %d parcelas sintéticas", len(service.parcels))
        except Exception:
            service.data_ready = False
            logger.exception("No se pudo inicializar el catálogo MOCK")
        yield

    app = FastAPI(title="Cebada360", version="0.1.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
    app.state.settings = config
    register_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
