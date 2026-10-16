export function CurvaCortesModelo({ cortes }) {
  if (!cortes || cortes.length === 0) return null;

  const rmseMax = Math.max(...cortes.map((c) => c.rmse));
  const rmseMin = Math.min(...cortes.map((c) => c.rmse));
  const span = rmseMax - rmseMin || 0.1;

  // Mejor R² alcanzado (octubre por lo general)
  const mejorR2 = Math.max(...cortes.map((c) => c.r2));

  return (
    <div>
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-text-hi">
          Desempeño por corte temporal
        </h2>
        <p className="mt-1 text-sm text-text-mid">
          ¿Qué tan temprano se puede anticipar el rendimiento final? Cada barra
          muestra el RMSE del modelo entrenado con datos hasta ese mes.
        </p>
      </div>

      {/* Gráfico */}
      <div className="grid grid-cols-4 gap-4 items-end h-56 px-2">
        {cortes.map((c, idx) => {
          // Altura relativa al RMSE (invertido: menor RMSE = barra más alta)
          const alturaNormalizada =
            (1 - (c.rmse - rmseMin) / span) * 65 + 25;

          const esMejor = c.rmse === rmseMin;

          return (
            <div key={c.corte} className="flex flex-col items-center gap-2 h-full justify-end">
              {/* Valor RMSE encima */}
              <span className="text-sm font-semibold text-text-hi tabular-nums">
                {c.rmse.toFixed(2)}
              </span>
              <span className="text-[10px] uppercase tracking-wide text-text-lo">
                RMSE
              </span>

              {/* Barra */}
              <div
                className={`w-full rounded-t-lg origin-bottom animate-grow-bar
                  ${esMejor
                    ? 'bg-gradient-to-t from-moss-700 to-moss-500'
                    : 'bg-gradient-to-t from-ink-800 to-ink-700'}`}
                style={{ height: `${alturaNormalizada}%`, animationDelay: `${idx * 80}ms` }}
              />

              {/* Etiqueta del corte */}
              <div className="text-center">
                <div className={`text-sm capitalize ${
                  esMejor ? 'text-moss-500 font-semibold' : 'text-text-mid'
                }`}>
                  {c.corte}
                </div>
                <div className="text-xs text-text-lo tabular-nums">
                  R² {c.r2.toFixed(2)} · {c.n_features} feat.
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Mensaje interpretativo */}
      <div className="mt-6 rounded-xl border border-ink-700/60 bg-ink-800/40 px-4 py-3">
        <div className="text-sm text-text-mid">
          <b className="text-text-hi">Mensaje clave:</b> con datos hasta{' '}
          <b className="text-moss-500">septiembre</b>, el modelo ya alcanza un
          R² de{' '}
          <b className="text-text-hi">
            {cortes.find((c) => c.corte === 'septiembre')?.r2.toFixed(2) ?? '—'}
          </b>{' '}
          ({(cortes.find((c) => c.corte === 'septiembre')?.r2 / mejorR2 * 100).toFixed(0)}%
          del techo del ciclo completo). Es decir, la predicción operativa puede
          entregarse <b className="text-moss-500">un mes antes del cierre</b>.
        </div>
      </div>
    </div>
  );
}