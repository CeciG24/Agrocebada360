const finite = (value) => typeof value === 'number' && Number.isFinite(value);
export function verifyModelEvidence(report, prediction) {
  if (report?.format_version !== 'model-evidence-v1' || !report.meta || report.meta.mode !== 'real'
    || !Array.isArray(report.features) || report.features.length !== report.n_features
    || !Array.isArray(report.oof?.points) || report.oof.points.length !== report.n_train
    || ![report.rmse, report.mae, report.r2].every(finite)
    || report.oof.points.some((p) => !finite(p.observed) || !finite(p.predicted))) throw new Error('Ficha inválida');
  const ref = report.reference_prediction;
  if (!ref || prediction.parcel_id !== ref.parcel_id || prediction.model_version !== report.model_version
    || prediction.model_version !== ref.model_version || prediction.unit !== ref.unit
    || !finite(prediction.prediction) || Math.abs(prediction.prediction - ref.prediction) > 1e-8
    || ['mode', 'cycle', 'data_cutoff', 'contract_version'].some((k) => prediction.meta[k] !== report.meta[k])) throw new Error('Ficha incompatible con la API activa');
  return report;
}
