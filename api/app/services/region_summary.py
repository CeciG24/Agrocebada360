"""Agregación por parcela sin dependencias de ML ni lecturas de archivos."""
import math

def summarize_regions(parcels, predictions, mode):
    from api.app.schemas.common import Meta
    from api.app.schemas.prediction import Prediction
    from api.app.schemas.regions import RegionSummary

    groups = {}
    for parcel_id, parcel in parcels.items():
        if parcel.region is not None:
            groups.setdefault(parcel.region, []).append(parcel_id)
    if set(predictions) - set(parcels):
        raise ValueError('Predicción fuera del catálogo.')
    validated = {key: Prediction.model_validate(value) for key, value in predictions.items()}
    if any(p.parcel_id != key or p.meta != Meta(mode=mode) for key, p in validated.items()):
        raise ValueError('ID u origen incompatible en el resumen regional.')
    summaries = {}
    for region, ids in groups.items():
        available = [validated[key] for key in ids if key in validated]
        if len({(p.model_version, p.unit) for p in available}) > 1:
            raise ValueError('No se mezclan modelos o unidades en una región.')
        summaries[region] = RegionSummary(
            region=region, parcel_count=len(ids), predicted_count=len(available),
            mean_prediction=math.fsum(p.prediction / len(available) for p in available) if available else None,
            unit=available[0].unit if available else None,
            model_version=available[0].model_version if available else None, meta=Meta(mode=mode))
    return summaries
