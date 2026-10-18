"""Nombres de presentación, acotados al modelo/schema auditados; fallback técnico."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
DICTIONARY_PATH = Path(__file__).resolve().parents[1] / 'catalogs/feature_labels.json'


def load_feature_labels(model_sha256, schema_sha256, *, path=None):
    try:
        document = json.loads(Path(path or DICTIONARY_PATH).read_text(encoding='utf-8'))
        if not isinstance(document, dict):
            raise ValueError('Diccionario inválido.')
        if document['dictionary_version'] != 'feature-labels-v1':
            raise ValueError('Versión de diccionario incompatible.')
        scope = document['scope']
        if not isinstance(scope, dict) or not isinstance(document['features'], dict):
            raise ValueError('Scope o features inválidos.')
        if scope['model_sha256'] != model_sha256 or scope['feature_schema_sha256'] != schema_sha256:
            logger.info('Diccionario fuera del modelo/schema: se conservan nombres técnicos.')
            return {}
        labels = {}
        for feature, record in document['features'].items():
            if not isinstance(record, dict):
                raise ValueError('Registro de variable inválido.')
            name = record['friendly_name']
            if not isinstance(feature, str) or not feature.strip() or not isinstance(name, str) or not name.strip():
                raise ValueError('Nombre de variable inválido.')
            labels[feature] = name
        return labels
    except (OSError, ValueError, TypeError, KeyError):
        logger.warning('Diccionario no disponible o inválido; se conservan nombres técnicos.')
        return {}
