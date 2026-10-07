import { fmtSigned } from '../../lib/format';

export function ShapBars({ items = [] }) {
  if (!items.length) return null;

  const max = Math.max(...items.map((i) => Math.abs(i.valor ?? 0)), 0.001);

  return (
    <div className="animate-fade-up">
      <div className="text-base text-text-mid mb-3">Qué mueve la estimación</div>
      <div className="space-y-2">
        {items.map((it, idx) => {
          const valor = it.valor ?? 0;
          const positivo = valor >= 0;
          const w = (Math.abs(valor) / max) * 100;
          return (
            <div
              key={it.categoria}
              className="grid grid-cols-[1fr_auto_auto] items-center gap-3 animate-fade-up"
              style={{ animationDelay: `${idx * 60}ms` }}
            >
              <span className="text-base text-text-hi truncate">{it.etiqueta ?? it.categoria}</span>
              <div className="h-1.5 w-24 rounded-full bg-ink-700 overflow-hidden">
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