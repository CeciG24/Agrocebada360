import { useState } from 'react';
import { fmtPct } from '../../lib/format';

const MIN_PARCELAS = 5;

export function TablaMunicipios({ municipios }) {
  const [soloConMuestra, setSoloConMuestra] = useState(false);

  const filtrados = soloConMuestra
    ? municipios.filter((m) => m.n_parcelas >= MIN_PARCELAS)
    : municipios;

  return (
    <div>
      {/* Toggle */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="text-base text-text-mid">
          Rendimiento esperado por municipio
        </div>
        <label className="inline-flex min-h-[40px] items-center gap-2 text-sm text-text-mid cursor-pointer select-none">
          <input
            type="checkbox"
            checked={soloConMuestra}
            onChange={(e) => setSoloConMuestra(e.target.checked)}
            className="h-4 w-4 cursor-pointer accent-moss-500"
          />
          Solo municipios con ≥ {MIN_PARCELAS} parcelas
        </label>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto -mx-2" tabIndex={0} role="region" aria-label="Tabla de municipios">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-text-lo">
              <th className="px-3 py-2 font-medium">Municipio</th>
              <th className="px-3 py-2 font-medium text-right">n</th>
              <th className="px-3 py-2 font-medium text-right">t/ha</th>
              <th className="hidden px-3 py-2 font-medium text-right sm:table-cell">Superficie</th>
              <th className="hidden px-3 py-2 font-medium text-right sm:table-cell">Producción</th>
              <th className="px-3 py-2 font-medium text-right">Riesgo alto</th>
            </tr>
          </thead>
          <tbody>
            {filtrados.map((m, idx) => (
              <tr
                key={m.municipio}
                className="border-t border-ink-700/50
                           transition-colors duration-150
                           hover:bg-ink-800/50
                           animate-fade-up"
                style={{ animationDelay: `${idx * 30}ms` }}
              >
                <td className="px-3 py-2.5 text-text-hi">{m.municipio}</td>
                <td className="px-3 py-2.5 text-right tabular-nums text-text-mid">
                  {m.n_parcelas}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-text-hi font-medium">
                  {m.rendimiento_promedio_t_ha.toFixed(2)}
                </td>
                <td className="hidden px-3 py-2.5 text-right tabular-nums text-text-mid sm:table-cell">
                  {m.superficie_total_ha.toFixed(1)} ha
                </td>
                <td className="hidden px-3 py-2.5 text-right tabular-nums text-text-mid sm:table-cell">
                  {m.produccion_total_t.toFixed(0)} t
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  <span
                    className={
                      m.distribucion_riesgo.alto >= 0.18
                        ? 'text-rose-400'
                        : m.distribucion_riesgo.alto >= 0.10
                          ? 'text-amber-400'
                          : 'text-moss-500'
                    }
                  >
                    {fmtPct(m.distribucion_riesgo.alto * 100)}
                  </span>
                </td>
              </tr>
            ))}
            {filtrados.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-text-lo text-sm">
                  Ningún municipio cumple el filtro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}