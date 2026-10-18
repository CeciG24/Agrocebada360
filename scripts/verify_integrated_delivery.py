"""Aceptación reproducible de los adaptadores, sin levantar API ni usar mocks."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from api.app.schemas.prediction import Prediction
from api.app.schemas.parcels import ParcelMapItem
from ml.integration import IntegratedArtifacts
from ml.inference import ParcelNotFound
from ml.model_bundle import read_json


def verify(data_root, delivery):
    artifacts = IntegratedArtifacts(data_root, delivery)
    ids = read_json(Path(__file__).resolve().parents[1] / 'ml/split/official_ids_v1.json')
    official = pd.read_csv(Path(__file__).resolve().parents[1] / 'ml/results/predictions_raw.csv').set_index('parcel_id')
    errors = []
    reconstruction = []
    for parcel_id in ids['eval_ids']:
        prediction = Prediction.model_validate(artifacts.predict(parcel_id))
        assert prediction.meta.mode == 'real' and prediction.lower is None
        errors.append(abs(prediction.prediction - official.loc[parcel_id, 'rendimiento_pred_t_ha']))
        interval = Prediction.model_validate(artifacts.predict(parcel_id, exploratory_intervals=True))
        assert interval.lower <= interval.prediction <= interval.upper
        explanation = artifacts.explain(parcel_id)
        assert explanation['status'] == 'available' and explanation['model_version'] == prediction.model_version
        assert explanation['output_space'] == prediction.unit
        assert len(explanation['features']) == 30
        reconstruction.append(abs(explanation['base_value'] + sum(f['impact'] for f in explanation['features']) - prediction.prediction))
        assert artifacts.risk(parcel_id)['status'] == 'unavailable'
    assert max(errors) < 1e-8 and max(reconstruction) < 1e-8
    assert artifacts.explain(ids['train_ids'][0])['reason'] == 'EXPLANATION_NOT_READY'
    for parcel in artifacts.catalog.values():
        ParcelMapItem.model_validate(parcel)
        assert parcel['region'] is None
    for method in [artifacts.predict, artifacts.explain, artifacts.risk]:
        try:
            method('unknown-id')
        except ParcelNotFound:
            pass
        else:
            raise AssertionError('ID inexistente fue aceptado.')
    return {'status': 'passed', 'n_parcels': len(artifacts.catalog), 'n_eval': len(errors),
            'n_geometries': sum(p['geometry'] is not None for p in artifacts.catalog.values()),
            'prediction_max_error': float(np.max(errors)),
            'explanation_max_error': float(np.max(reconstruction)),
            'model_version': artifacts.pipeline.model_version,
            'mode': 'real', 'api_activated': False, 'risk_available': False,
            'intervals_default': False, 'unknown_ids_rejected': True,
            'train_explanation_unavailable': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', required=True)
    parser.add_argument('--delivery', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    report = verify(args.data_root, args.delivery)
    Path(args.report).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
