export function TablaAblacion({ ablacion }) {
  if (!ablacion || ablacion.length === 0) return null;

  // La fila de "Fusión" es la referencia (delta = 0)
  const fusion = ablacion.find((a) => a.familia === 'Fusión');
  const rmseReferencia = fusion?.rmse ?? Math.min(...ablacion.map((a) => a.rmse));

  return (
    <div>
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-text-hi">
          Aporte de cada familia de features
        </h2>
        <p className="mt-1 text-sm text-text-mid">
          Se entrena el modelo eliminando una familia a la vez. Si el RMSE sube
          mucho al quitarla, esa familia aportaba información valiosa. Si apenas
          cambia, no aporta.
        </p>
      </div>

      <div className="space-y-3">
        {ablacion.map((a, idx) => {
          const esFusion = a.familia === 'Fusión';
          const delta = a.delta_rmse ?? (a.rmse - rmseReferencia);
          const aporte = Math.max(0, delta);
          const maxAporte = Math.max(
            ...ablacion.map((x) => Math.max(0, x.delta_rmse ?? 0)),
            0.01,
          );
          const w = (aporte / maxAporte) * 100;

          return (
            <div
              key={a.familia}
              className={`rounded-xl border px-4 py-3 animate-fade-up
                ${esFusion
                  ? 'border-moss-700/40 bg-moss-900/20'
                  : 'border-ink-700/60 bg-ink-800/40'}`}
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <div className="grid grid-cols-[96px_1fr_auto] items-center gap-3 sm:grid-cols-[140px_1fr_auto] sm:gap-4">
                <span className={`text-sm ${esFusion ? 'text-moss-500 font-semibold' : 'text-text-hi'}`}>
                  {a.familia}
                </span>

                <div className="h-2 rounded-full bg-ink-700 overflow-hidden">
                  <div
                    className={`h-full origin-left animate-grow-bar ${
                      esFusion ? 'bg-moss-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${w}%` }}
                  />
                </div>

                <span className="text-sm tabular-nums text-text-mid w-20 sm:w-24 text-right">
                  {esFusion
                    ? `RMSE ${a.rmse.toFixed(2)}`
                    : `+${delta.toFixed(2)}`}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <p className="mt-4 text-xs text-text-lo">
        Valores en t/ha. Un <b className="text-text-mid">+0.19</b> significa
        que el RMSE empeora 0.19 t/ha cuando esa familia se elimina.
      </p>
    </div>
  );
}