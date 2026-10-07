import { colorPorRendimiento } from '../../lib/colores';

export function MiniMapaContexto({ parcela, vecinos }) {
  const todos = [parcela, ...vecinos];
  return (
    <div>
      <div className="text-base text-text-mid mb-3">Contexto en el municipio</div>
      <div className="grid grid-cols-4 gap-2">
        {todos.map((p, i) => {
          const esActual = i === 0;
          return (
            <div
              key={p.id}
              style={{ backgroundColor: colorPorRendimiento(p.rendimiento_t_ha) }}
              className={`aspect-square rounded-lg grid place-items-center text-xs font-semibold text-white/90 ${
                esActual ? 'ring-2 ring-white' : 'ring-1 ring-white/10'
              }`}
            >
              {p.id.split('_')[1]}
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-sm text-text-lo">
        Esta parcela frente a {vecinos.length} vecinas del mismo municipio.
      </p>
    </div>
  );
}