import { fmtT } from '../../lib/format';

export function ComparacionVecinos({ vecinos, actualId }) {
  if (!vecinos || vecinos.length === 0) return null;

  const max = Math.max(...vecinos.map((v) => v.rendimiento_t_ha), 0.001);

  return (
    <div className="animate-fade-up">
      <div className="text-base text-text-mid mb-3">Parcelas similares en el municipio</div>
      <div className="space-y-2 stagger">
        {vecinos.map((v) => {
          const w = (v.rendimiento_t_ha / max) * 100;
          return (
            <div
              key={v.id}
              className={`grid grid-cols-[80px_1fr_auto] items-center gap-3 rounded-lg px-3 py-2
                          transition-all duration-200 hover:bg-ink-800
                ${v.id === actualId ? 'bg-moss-900/40 border border-moss-700/40' : 'bg-ink-800/50'}`}
            >
              <span className="text-sm text-text-hi font-mono">{v.id.split('_')[1]}</span>
              <div className="h-1.5 rounded-full bg-ink-700 overflow-hidden">
                <div
                  className="h-full bg-moss-600 origin-left animate-grow-bar"
                  style={{ width: `${w}%` }}
                />
              </div>
              <span className="text-sm tabular-nums text-text-mid">{fmtT(v.rendimiento_t_ha)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}