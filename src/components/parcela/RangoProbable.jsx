import { esNum } from '../../lib/format';

export function RangoProbable({ estimado, rango }) {
  const valido = Array.isArray(rango) && rango.length === 2 && rango.every(esNum) && esNum(estimado);
  if (!valido) {
    return <p className="text-sm text-text-lo">Rango probable no disponible.</p>;
  }
  const [lo, hi] = rango;

  const min = 2.0;
  const max = 6.0;
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
        <span>2.0</span><span>4.0</span><span>6.0 t/ha</span>
      </div>
      <p className="mt-2 text-base text-text-mid">
        Entre <b className="text-text-hi">{lo.toFixed(2)}</b> y{' '}
        <b className="text-text-hi">{hi.toFixed(2)}</b> t/ha
      </p>
    </div>
  );
}