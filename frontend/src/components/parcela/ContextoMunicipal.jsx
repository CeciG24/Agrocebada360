import { fmtT, fmtTons, esNum } from '../../lib/format';
import { regionLabel } from '../../lib/regions';

export function ContextoMunicipal({ contexto, parcela }) {
  if (!contexto) return null;

  if ('region' in contexto) return (
    <div className="space-y-3">
      <h3 className="text-base text-text-mid">Región {regionLabel(contexto.region)}</h3>
      <p>Cobertura: {contexto.predicted_count} / {contexto.parcel_count} parcelas con predicción.</p>
      <p>Media por parcela: {contexto.predicted_count > 0 ? `${contexto.mean_prediction.toFixed(4)} ${contexto.unit}` : 'no disponible'}.</p>
      {contexto.model_version && <p className="text-sm text-text-lo">Modelo {contexto.model_version}</p>}
      {contexto.meta?.mode === 'real' && <p className="text-sm text-text-lo">Media de las predicciones de evaluación del dataset; no representa a todos los productores de la región.</p>}
    </div>
  );

  // La comparación solo existe si ambos rendimientos son números válidos.
  const diferencia =
    esNum(parcela?.rendimiento_t_ha) && esNum(contexto.rendimiento_promedio_t_ha)
      ? parcela.rendimiento_t_ha - contexto.rendimiento_promedio_t_ha
      : null;
  const signo = diferencia !== null && diferencia >= 0 ? 'por encima' : 'por debajo';

  return (
    <div className="space-y-4">
      <div className="text-base text-text-mid">Contexto municipal — {contexto.municipio ?? 'municipio no disponible'}</div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="rounded-lg bg-ink-800/60 px-3 py-2">
          <div className="text-text-lo text-xs">Parcelas</div>
          <div className="text-text-hi font-semibold">{contexto.n_parcelas ?? '—'}</div>
        </div>
        <div className="rounded-lg bg-ink-800/60 px-3 py-2">
          <div className="text-text-lo text-xs">Promedio</div>
          <div className="text-text-hi font-semibold">{fmtT(contexto.rendimiento_promedio_t_ha)}</div>
        </div>
        <div className="rounded-lg bg-ink-800/60 px-3 py-2">
          <div className="text-text-lo text-xs">Producción</div>
          <div className="text-text-hi font-semibold">{fmtTons(contexto.produccion_total_t)}</div>
        </div>
      </div>

      {diferencia !== null && (
        <p className="text-sm text-text-mid">
          Esta parcela está{' '}
          <b className={diferencia >= 0 ? 'text-moss-500' : 'text-rose-400'}>
            {fmtT(Math.abs(diferencia))} {signo}
          </b>{' '}
          del promedio municipal.
        </p>
      )}

      {Array.isArray(contexto.factores_limitantes) && contexto.factores_limitantes.length > 0 && (
        <div>
          <div className="text-sm text-text-lo mb-2">Factores limitantes predominantes</div>
          <div className="flex flex-wrap gap-2">
            {contexto.factores_limitantes.map((f) => (
              <span
                key={f}
                className="rounded-full bg-ink-800/70 border border-ink-700/60 px-3 py-1 text-xs text-text-mid"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
