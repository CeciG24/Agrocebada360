import { fmtSigned, esNum } from '../../lib/format';

export function FeatureHighlights({ items = [], context }) {
  const top = items.filter((item) => esNum(item.valor)).slice().sort((a, b) => Math.abs(b.valor) - Math.abs(a.valor)).slice(0, 3);
  const maximum = Math.max(...top.map((item) => Math.abs(item.valor)), 0.001);
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((i) => {
        const item = top[i];
        return item ? (
          <div key={item.categoria} className="factor-row">
            <span className="factor-rank" aria-hidden="true">0{i + 1}</span>
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-2">
                <p className="break-words text-sm font-medium text-text-hi">{item.etiqueta ?? item.categoria}</p>
                <span className={`shrink-0 text-sm font-semibold tabular-nums ${item.valor > 0 ? 'text-moss-500' : item.valor < 0 ? 'text-rose-400' : 'text-text-mid'}`}>{fmtSigned(item.valor)}</span>
              </div>
              <div className="mt-2 h-1 overflow-hidden rounded-full bg-ink-700" aria-hidden="true">
                <div className={`h-full rounded-full ${item.valor < 0 ? 'bg-rose-400' : 'bg-moss-500'}`} style={{ width: `${Math.abs(item.valor) / maximum * 100}%` }} />
              </div>
              <p className="mt-1 text-xs text-text-mid">{item.valor > 0 ? 'Contribuye al alza' : item.valor < 0 ? 'Contribuye a la baja' : 'Contribución neutral'}</p>
            </div>
          </div>
        ) : (
          <div key={`pending-${i}`} className="factor-row border-dashed">
            <span className="factor-rank" aria-hidden="true">0{i + 1}</span>
            <div className="min-w-0 flex-1"><p className="text-xs text-text-mid">Factor {i + 1} pendiente</p><div className="mt-2 h-1 rounded-full bg-ink-700" aria-hidden="true" /></div>
            <span className="text-text-mid" aria-hidden="true">—</span>
          </div>
        );
      })}
      <p className="text-xs leading-relaxed text-text-mid">{top.length > 0
        ? `Principales contribuciones por magnitud${context?.output_space ? ` · escala ${context.output_space}` : ''}. No describen efectos causales.`
        : 'Los factores aparecerán cuando la fuente entregue una explicación de esta predicción.'}</p>
    </div>
  );
}
