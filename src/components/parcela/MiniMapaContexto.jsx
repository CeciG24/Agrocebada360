import { colorPorRendimiento } from '../../lib/colores';
import { esNum } from '../../lib/format';
import { useTamanoPx } from '../../lib/useTamanoPx';
import {
  validarGeometrias,
  crearProyeccion,
  anillosAPath,
  centroide,
  anchoBBox,
} from '../../lib/geo';

const NEUTRO = '#2a3530';
const codigoDe = (id) => String(id ?? '').split('_')[1] ?? String(id ?? '?');
const colorDe = (p) => (esNum(p?.rendimiento_t_ha) ? colorPorRendimiento(p.rendimiento_t_ha) : NEUTRO);

// Respaldo cuando no hay geometrías de esta parcela: cuadritos por rendimiento.
function Cuadritos({ todos }) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {todos.map((p, i) => {
        const esActual = i === 0;
        return (
          <div
            key={p.id}
            style={{ backgroundColor: colorDe(p) }}
            className={`aspect-square rounded-lg grid place-items-center text-xs font-semibold text-white/90 ${
              esActual ? 'ring-2 ring-white' : 'ring-1 ring-white/10'
            }`}
          >
            {codigoDe(p.id)}
          </div>
        );
      })}
    </div>
  );
}

export function MiniMapaContexto({ parcela, vecinos, geometrias }) {
  const lista = Array.isArray(vecinos) ? vecinos.filter((v) => v && v.id) : [];
  const todos = [parcela, ...lista];

  // Solo se dibujan las parcelas que tienen geometría válida. Sin la geometría
  // de la parcela actual no hay mapa que mostrar: se usa el respaldo.
  const ids = new Set(todos.map((p) => p.id));
  const { features } = validarGeometrias(geometrias);
  const presentes = features.filter((f) => ids.has(f.id));
  const proy = presentes.some((f) => f.id === parcela.id)
    ? crearProyeccion(presentes, { ancho: 400, margen: 16 })
    : null;

  const [svgRef, tam] = useTamanoPx(Boolean(proy));
  const pxPorUnidad = proy ? Math.max(Math.min(tam.w / proy.ancho, tam.h / proy.alto), 1e-6) : 1;

  let formas = [];
  if (proy) {
    formas = presentes.map((f) => ({
      id: f.id,
      sintetica: f.sintetica,
      d: anillosAPath(f.anillos, proy.project),
      centro: centroide(f.anillos, proy.project),
      ancho: anchoBBox(f.anillos, proy.project),
    }));
    // La parcela actual se dibuja al final para que su borde quede encima.
    formas.sort((a, b) => (a.id === parcela.id) - (b.id === parcela.id));
  }

  const porId = new Map(todos.map((p) => [p.id, p]));
  const sinGeometria = proy ? lista.filter((v) => !presentes.some((f) => f.id === v.id)).length : 0;
  const haySinteticas = formas.some((f) => f.sintetica);

  return (
    <div>
      <div className="text-base text-text-mid mb-3">Contexto en el municipio</div>

      {proy ? (
        <div className="rounded-xl border border-ink-700/60 bg-ink-950 p-2">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${proy.ancho} ${proy.alto}`}
            preserveAspectRatio="xMidYMid meet"
            role="img"
            aria-label={`Mapa de la parcela ${parcela.id} y ${formas.length - 1} vecinas`}
            className="block w-full"
            style={{ maxHeight: 280 }}
          >
            {formas.map((f) => {
              const actual = f.id === parcela.id;
              return (
                <path
                  key={f.id}
                  d={f.d}
                  fillRule="evenodd"
                  fill={colorDe(porId.get(f.id))}
                  stroke={actual ? '#ffffff' : '#3f6b4f'}
                  strokeWidth={actual ? 3 : 1.25}
                  vectorEffect="non-scaling-stroke"
                  strokeLinejoin="round"
                />
              );
            })}
            {formas.map((f) =>
              f.ancho * pxPorUnidad > 28 ? (
                <text
                  key={`t-${f.id}`}
                  x={f.centro[0]}
                  y={f.centro[1]}
                  fontSize={12 / pxPorUnidad}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill="rgba(255,255,255,0.92)"
                  fontWeight="600"
                  pointerEvents="none"
                >
                  {codigoDe(f.id)}
                </text>
              ) : null,
            )}
          </svg>
        </div>
      ) : (
        <Cuadritos todos={todos} />
      )}

      <p className="mt-3 text-sm text-text-lo">
        Esta parcela frente a {lista.length} vecinas del mismo municipio.
        {proy && ' El contorno blanco marca esta parcela.'}
      </p>
      {sinGeometria > 0 && (
        <p className="mt-1 text-xs text-text-lo">
          {sinGeometria === 1
            ? '1 vecina sin geometría no aparece en el mapa.'
            : `${sinGeometria} vecinas sin geometría no aparecen en el mapa.`}
        </p>
      )}
      {haySinteticas && (
        <p className="mt-1 text-xs text-amber-400/90">
          Geometrías sintéticas de demostración: no son los polígonos oficiales.
        </p>
      )}
    </div>
  );
}