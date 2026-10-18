import { fmtSigned } from '../../lib/format';

export function ShapBars({ items = [], context }) {
  if (!items.length) {
    return <p className="text-sm text-text-lo">Sin explicación disponible para esta parcela.</p>;
  }

  const max = Math.max(...items.map((i) => Math.abs(i.valor ?? 0)), 0.001);

  return (
    <div className="animate-fade-up">
      <div className="text-base text-text-mid mb-3">Qué mueve la estimación</div>
      {context && <p className="mb-3 text-sm text-text-lo">{context.method} · modelo {context.model_version} · escala {context.output_space} · referencia {context.base_value} · salida explicada {context.explained_output}</p>}
      {context && <p className="mb-3 text-xs text-text-mid">Los impactos están en {context.output_space}. Son contribuciones del modelo, no efectos causales.</p>}
      <div className="space-y-2">
        {items.map((it, idx) => {
          const valor = it.valor ?? 0;
          const positivo = valor >= 0;
          const w = (Math.abs(valor) / max) * 100;
          return (
            <div
              key={it.categoria}
              className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1.5 sm:grid-cols-[1fr_auto_auto] animate-fade-up"
              style={{ animationDelay: `${idx * 60}ms` }}
            >
              <div className="min-w-0 break-words text-base text-text-hi" title={it.categoria}>
                <span>{it.etiqueta ?? it.categoria}</span>
                {it.etiqueta && it.etiqueta !== it.categoria && <details className="mt-1 text-xs text-text-mid">
                  <summary className="cursor-pointer">Variable técnica<span className="sr-only"> de {it.etiqueta}</span></summary>
                  <code className="mt-1 block break-all">{it.categoria}</code>
                </details>}
              </div>
              <div className="order-last col-span-2 h-1.5 w-full rounded-full bg-ink-700 overflow-hidden sm:order-none sm:col-span-1 sm:w-24">
                <div
                  className={`h-full origin-left animate-grow-bar
                    ${positivo ? 'bg-moss-500' : 'bg-rose-500'}`}
                  style={{ width: `${w}%`, animationDelay: `${idx * 60 + 100}ms` }}
                />
              </div>
              <span className={`w-16 text-right text-sm tabular-nums ${positivo ? 'text-moss-500' : 'text-rose-400'}`}>
                {fmtSigned(valor)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
