import { esNum } from '../../lib/format';

export function RangoProbable({ estimado, rango, unit = 't/ha', level, method }) {
  const valido = Array.isArray(rango) && rango.length === 2 && rango.every(esNum) && esNum(estimado)
    && rango[0] <= estimado && estimado <= rango[1];
  if (!valido) {
    return <p className="text-sm text-text-lo">Rango probable no disponible.</p>;
  }
  const [lo, hi] = rango;

  const margen = Math.max((hi - lo) * 0.15, Math.abs(estimado) * 0.01, 0.01);
  const min = lo - margen;
  const max = hi + margen;
  const pct = (v) => Math.max(0, Math.min(100, ((v - min) / (max - min)) * 100));

  return (
    <div className="animate-fade-up">
      <div className="text-base text-text-mid mb-2">Rango probable</div>
      <div className="relative h-6">
        <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-ink-600" />
        <div
          className="absolute top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-moss-600/70
                     transition-all duration-500 ease-out"
          style={{ left: `${pct(lo)}%`, width: `${pct(hi) - pct(lo)}%` }}
        />
        <div
          className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full
                     bg-moss-500 ring-4 ring-moss-500/20
                     transition-all duration-500 ease-out
                     hover:scale-125"
          style={{ left: `${pct(estimado)}%` }}
        />
      </div>
      <div className="mt-2 flex justify-between text-sm text-text-lo">
        <span>{min.toFixed(2)}</span><span>{((min + max) / 2).toFixed(2)}</span><span>{max.toFixed(2)} {unit}</span>
      </div>
      <p className="mt-2 text-base text-text-mid">
        Entre <b className="text-text-hi">{lo.toFixed(2)}</b> y{' '}
        <b className="text-text-hi">{hi.toFixed(2)}</b> {unit}
      </p>
      {method && <p className="text-sm text-text-lo">Método: {method} · cobertura nominal {esNum(level) ? `${(level * 100).toFixed(1)}%` : 'no disponible'}. No es una garantía individual.</p>}
    </div>
  );
}
