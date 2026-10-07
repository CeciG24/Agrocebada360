const COLORES = {
  bajo:  'bg-moss-500',
  medio: 'bg-amber-500',
  alto:  'bg-rose-500',
};

const ETIQUETA = { bajo: 'Bajo', medio: 'Medio', alto: 'Alto' };

export function DistribucionRiesgo({ municipios }) {
  if (!municipios || municipios.length === 0) return null;

  return (
    <div>
      {/* Leyenda */}
      <div className="flex items-center gap-4 text-xs text-text-mid mb-4">
        {Object.entries(COLORES).map(([k, c]) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-sm ${c}`} />
            Riesgo {ETIQUETA[k]}
          </span>
        ))}
      </div>

      {/* Filas */}
      <div className="space-y-3">
        {municipios.map((m, idx) => {
          const r = m.distribucion_riesgo;
          return (
            <div
              key={m.municipio}
              className="grid grid-cols-[140px_1fr_60px] items-center gap-3
                         animate-fade-up"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <span className="text-sm text-text-hi truncate">{m.municipio}</span>

              <div className="flex h-5 rounded-md overflow-hidden bg-ink-800">
                <div
                  className={`${COLORES.bajo} origin-left animate-grow-bar`}
                  style={{ width: `${r.bajo * 100}%` }}
                  title={`Bajo: ${(r.bajo * 100).toFixed(0)}%`}
                />
                <div
                  className={`${COLORES.medio} origin-left animate-grow-bar`}
                  style={{ width: `${r.medio * 100}%`, animationDelay: '80ms' }}
                  title={`Medio: ${(r.medio * 100).toFixed(0)}%`}
                />
                <div
                  className={`${COLORES.alto} origin-left animate-grow-bar`}
                  style={{ width: `${r.alto * 100}%`, animationDelay: '160ms' }}
                  title={`Alto: ${(r.alto * 100).toFixed(0)}%`}
                />
              </div>

              <span className="text-xs text-text-lo text-right tabular-nums">
                {m.n_parcelas} p.
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}