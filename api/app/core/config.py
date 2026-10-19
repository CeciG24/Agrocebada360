"""Configuración explícita de origen; el modo predeterminado sigue siendo mock."""

import os
from typing import Literal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: Literal["mock", "real"] = "mock"
    data_root: Path | None = None
    delivery_path: Path | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    allowed_origins: str = ""  # lista separada por comas, p.ej. "https://app.vercel.app"

    @model_validator(mode="after")
    def real_paths(self):
        if self.mode == "real" and (self.data_root is None or self.delivery_path is None):
            raise ValueError("El modo real requiere CEBADA_DATA y CEBADA_DELIVERY explícitos.")
        return self


def get_settings() -> Settings:
    return Settings(mode=os.getenv("CEBADA_MODE", "mock"),
                    data_root=os.getenv("CEBADA_DATA") or None,
                    delivery_path=os.getenv("CEBADA_DELIVERY") or None,
                    log_level=os.getenv("CEBADA_LOG_LEVEL", "INFO").upper(),
                    allowed_origins=os.getenv("CEBADA_ALLOWED_ORIGINS", ""))
