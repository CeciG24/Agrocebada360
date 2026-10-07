import { MetricaCard } from './MetricaCard';

const METRICAS = [
  { key: 'rmse', label: 'RMSE', unit: 't/ha', formato: (v) => v.toFixed(2), mejorMenor: true },
  { key: 'mae',  label: 'MAE',  unit: 't/ha', formato: (v) => v.toFixed(2), mejorMenor: true },
  { key: 'r2',   label: 'R²',   unit: null,   formato: (v) => v.toFixed(2), mejorMenor: false },
];

function Columna({ titulo, subtitulo, datos, otra }) {
  return (
    <div className="space-y-4">
      <div>
        <div className="text-base font-semibold text-text-hi">{titulo}</div>
        <div className="text-xs text-text-lo mt-0.5">{subtitulo}</div>
      </div>

      <div className="space-y-3">
        {METRICAS.map((m) => {
          const valor = datos[m.key];
          const valorOtra = otra[m.key];
          const esMejor = m.mejorMenor
            ? valor < valorOtra
            : valor > valorOtra;

          return (
            <div
              key={m.key}
              className="flex items-center justify-between rounded-lg border border-ink-700/60
                         bg-ink-800/50 px-4 py-3"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm text-text-mid">{m.label}</span>
                {esMejor && (
                  <span className="rounded-full bg-moss-900/60 border border-moss-700/40
                                   px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide
                                   text-moss-500">
                    mejor
                  </span>
                )}
              </div>
              <span className="text-lg font-semibold text-text-hi tabular-nums">
                {m.formato(valor)}
                {m.unit && <span className="ml-1 text-xs text-text-lo">{m.unit}</span>}
              </span>
            </div>
          );
        })}

        <div className="flex items-center justify-between rounded-lg border border-ink-700/40
                        bg-ink-800/30 px-4 py-2.5">
          <span className="text-xs text-text-lo">Desviación entre folds</span>
          <span className="text-sm text-text-mid tabular-nums">± {datos.std.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

export function ComparacionCV({ cvAleatoria, cvEspacial }) {
  if (!cvAleatoria || !cvEspacial) return null;

  return (
    <div>
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-text-hi">
          Validación aleatoria vs. validación espacial
        </h2>
        <p className="mt-1 text-sm text-text-mid">
          La CV aleatoria mide qué tan bien predice el modelo dentro de la misma zona.
          La CV espacial mide qué tan bien generaliza a zonas que no vio durante el entrenamiento.
          La diferencia entre ambas es la prueba de rigor del modelo.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Columna
          titulo="CV aleatoria"
          subtitulo="Parcelas repartidas al azar entre folds"
          datos={cvAleatoria}
          otra={cvEspacial}
        />
        <Columna
          titulo="CV espacial"
          subtitulo="Grupos por municipio (parcelas vecinas juntas)"
          datos={cvEspacial}
          otra={cvAleatoria}
        />
      </div>

      <div className="mt-5 rounded-xl border border-amber-700/30 bg-amber-950/20 px-4 py-3 text-sm text-amber-200/90">
        <b className="text-amber-200">Cómo leerlo:</b> una caída moderada de desempeño
        entre ambas validaciones es esperable y honesta. Si la diferencia fuera muy
        grande, el modelo estaría memorizando zonas en lugar de aprender patrones.
      </div>
    </div>
  );
}