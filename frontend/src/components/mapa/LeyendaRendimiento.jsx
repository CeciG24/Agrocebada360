import { COLOR_SIN_RESULTADO } from '../../lib/colores';

export function LeyendaRendimiento() {
  const stops = ['#0f2a1a', '#14532d', '#166534', '#15803d', '#16a34a'];
  const clip = 'polygon(8% 12%, 94% 4%, 96% 92%, 4% 96%)';

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-text-mid" aria-label="Leyenda: verde de menor a mayor rendimiento; gris sin resultado cargado; borde blanco para selección">
      <span>Menor</span>
      <div className="flex gap-1">
        {stops.map((c) => (
          <span
            key={c}
            className="h-3.5 w-6"
            style={{ backgroundColor: c, clipPath: clip }}
          />
        ))}
      </div>
      <span>Mayor rendimiento</span>
      <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-sm border border-[#82958a]" style={{ backgroundColor: COLOR_SIN_RESULTADO }} aria-hidden="true" />Sin resultado cargado</span>
      <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-sm border-2 border-white" aria-hidden="true" />Selección</span>
    </div>
  );
}
