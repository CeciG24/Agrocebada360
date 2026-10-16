import { esNum } from '../../lib/format';

export function CurvaCortes({ cortes, corteActual }) {
  // Solo se dibujan cortes con rendimiento válido.
  const validos = Array.isArray(cortes) ? cortes.filter((c) => c && esNum(c.rendimiento_t_ha)) : [];
  if (validos.length === 0) return null;

  const max = Math.max(...validos.map((c) => c.rendimiento_t_ha));
  const min = Math.min(...validos.map((c) => c.rendimiento_t_ha));
  const span = max - min || 1;

  return (
    <div className="animate-fade-up">
      <div className="text-base text-text-mid mb-3">Predicción a lo largo del ciclo</div>
      <div className="flex items-end gap-2 h-32">
        {validos.map((c, idx) => {
          const h = ((c.rendimiento_t_ha - min) / span) * 60 + 40;
          const activo = c.corte === corteActual;
          return (
            <div key={c.corte} className="flex-1 flex flex-col items-center gap-2">
              <span className="text-xs text-text-mid tabular-nums">
                {c.rendimiento_t_ha.toFixed(2)}
              </span>
              <div
                className={`w-full rounded-t-md origin-bottom animate-grow-bar transition-colors duration-300
                  ${activo ? 'bg-moss-500' : 'bg-moss-700/60 hover:bg-moss-700'}`}
                style={{ height: `${h}%`, animationDelay: `${idx * 80}ms` }}
              />
              <span className={`text-xs capitalize transition-colors duration-300
                ${activo ? 'text-moss-500 font-semibold' : 'text-text-lo'}`}>
                {c.corte}
              </span>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-sm text-text-lo">
        A medida que avanza el ciclo, la predicción gana precisión.
      </p>
    </div>
  );
}