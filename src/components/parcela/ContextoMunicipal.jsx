import { fmtT, fmtHa, fmtTons, fmtPct } from '../../lib/format';

export function ContextoMunicipal({ contexto, parcela }) {
  if (!contexto) return null;

  const diferencia = parcela.rendimiento_t_ha - contexto.rendimiento_promedio_t_ha;
  const signo = diferencia >= 0 ? 'por encima' : 'por debajo';

  return (
    <div className="space-y-4">
      <div className="text-base text-text-mid">Contexto municipal — {contexto.municipio}</div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="rounded-lg bg-ink-800/60 px-3 py-2">
          <div className="text-text-lo text-xs">Parcelas</div>
          <div className="text-text-hi font-semibold">{contexto.n_parcelas}</div>
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

      <p className="text-sm text-text-mid">
        Esta parcela está{' '}
        <b className={diferencia >= 0 ? 'text-moss-500' : 'text-rose-400'}>
          {fmtT(Math.abs(diferencia))} {signo}
        </b>{' '}
        del promedio municipal.
      </p>

      {contexto.factores_limitantes?.length > 0 && (
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