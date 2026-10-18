"""Fixtures compartidas. Los tests que necesitan el dataset real se OMITEN (skip) si no existe; nunca cargan datos al importar."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session")
def data():
    from src import config as C
    if not (C.DATA_ROOT / "features" / "features_master.csv").exists():
        pytest.skip(f"no hay dataset en {C.DATA_ROOT} (define CEBADA_DATA)")
    from src.data import load
    return load()


@pytest.fixture(scope="session")
def tr(data):
    return data[0]


@pytest.fixture(scope="session")
def ev(data):
    return data[1]
