"""Configuración inicial: únicamente modo mock, sin artefactos ML."""

import os
from typing import Literal

from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: Literal["mock"] = "mock"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


def get_settings() -> Settings:
    return Settings(log_level=os.getenv("CEBADA_LOG_LEVEL", "INFO").upper())
