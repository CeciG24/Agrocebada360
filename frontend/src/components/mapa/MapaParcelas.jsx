import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Panel } from '../common/Panel';
import { LeyendaRendimiento } from './LeyendaRendimiento';
import { colorPorRendimiento, COLOR_SIN_RESULTADO } from '../../lib/colores';
import { construirProyeccion, procesarGeometria } from '../../lib/geo';
import { useTamanoPx } from '../../lib/useTamanoPx';
// ---------- Constantes ----------
const SIN_DATO = COLOR_SIN_RESULTADO;
const COLOR_RIESGO = { bajo: '#15803d', medio: '#b45309', alto: '#b91c1c' };
const ETIQUETA_RIESGO = { bajo: 'Riesgo bajo', medio: 'Riesgo medio', alto: 'Riesgo alto' };
const ETIQUETA_REVISION = { bajo: 'Sin alerta combinada', medio: 'Revisión media', alto: 'Prioridad alta' };
const K_MIN = 1;
const K_MAX = 32;
const VISTA_INICIAL = { k: 1, x: 0, y: 0 };
const DIRECCIONES = {
  ArrowRight: [1, 0],
  ArrowLeft: [-1, 0],
  ArrowDown: [0, 1],
  ArrowUp: [0, -1],
};

const limitar = (v, a, b) => Math.min(b, Math.max(a, v));
const idDe = (el) => el?.closest?.('[data-id]')?.dataset.id ?? null;

// Evita que el mapa se pueda arrastrar fuera de la vista.
function ajustar(v, proy) {
  return {
    k: v.k,
    x: limitar(v.x, proy.ancho * (1 - v.k), 0),
    y: limitar(v.y, proy.alto * (1 - v.k), 0),
  };
}

// Parcela vecina más cercana en la dirección de la flecha (solo con datos).
function vecinoEn(items, actualId, [dx, dy], porId) {
  const actual = items.find((it) => it.id === actualId);
  if (!actual) return null;
  let mejor = null;
  let mejorCosto = Infinity;
  for (const it of items) {
    if (it.id === actualId || !porId.has(it.id)) continue;
    const vx = it.cx - actual.cx;
    const vy = it.cy - actual.cy;
    const along = vx * dx + vy * dy;
    if (along <= 0) continue;
    const costo = along + 2 * Math.abs(vx * dy - vy * dx);
    if (costo < mejorCosto) {
      mejorCosto = costo;
      mejor = it.id;
    }
  }
  return mejor;
}

// ---------- Capa de polígonos (memoizada: no se redibuja al mover el mouse) ----------
const CapaParcelas = memo(function CapaParcelas({ items, colores, tabbableId, seleccionadaId }) {
  return (
    <g strokeWidth="0.85" strokeLinejoin="round" fillRule="evenodd">
      {items.map((it) => (
        <path
          key={it.id}
          data-id={it.id}
          d={it.d}
          fill={colores.get(it.id) ?? SIN_DATO}
          stroke={colores.has(it.id) ? '#b1cdbb' : '#82958a'}
          vectorEffect="non-scaling-stroke"
          role="button"
          aria-label={it.etiqueta}
          aria-pressed={it.id === seleccionadaId}
          tabIndex={it.id === tabbableId ? 0 : -1}
          className="cursor-pointer outline-none"
        />
      ))}
    </g>
  );
});

// ---------- Botón de control ----------
function BotonControl({ children, etiqueta, onClick, disabled }) {
  return (
    <button
      type="button"
      aria-label={etiqueta}
      title={etiqueta}
      onClick={onClick}
      disabled={disabled}
      className="grid h-10 w-10 place-items-center rounded-lg border border-ink-600 bg-ink-900/90 sm:h-9 sm:w-9
                 text-lg leading-none text-text-hi transition-colors
                 hover:bg-ink-700 disabled:opacity-35 disabled:hover:bg-ink-900/90"
    >
      {children}
    </button>
  );
}

// ============================================================
// Mapa de parcelas: polígonos reales como SVG (sin tiles → funciona offline)
// ============================================================
export function MapaParcelas({ parcelas, geometrias, seleccionadaId, onSelect, onAbrir }) {
  const etiquetasRiesgo = parcelas.some((p) => p.risk_method_version) ? ETIQUETA_REVISION : ETIQUETA_RIESGO;
  const [modo, setModo] = useState('rendimiento'); // 'rendimiento' | 'riesgo'
  const [vista, setVista] = useState(VISTA_INICIAL);
  const [hover, setHover] = useState(null); // { id, x, y, flip }

  const [svgRef, tamano] = useTamanoPx();
  const cajaRef = useRef(null);
  const arrastre = useRef(null);
  const movido = useRef(false);

  const sintetica = Boolean(geometrias.properties?.sintetica);

  const proy = useMemo(() => construirProyeccion(geometrias.features), [geometrias]);
  const porId = useMemo(() => new Map(parcelas.map((p) => [p.id, p])), [parcelas]);

  // Geometría ya proyectada + texto accesible de cada parcela
  const items = useMemo(() => {
    if (!proy) return [];
    const lista = [];
    for (const f of geometrias.features) {
      const id = String(f?.properties?.id ?? f?.id ?? '');
      const g = id ? procesarGeometria(f.geometry, proy.proyectar) : null;
      if (!g) continue;
      const p = porId.get(id);
      lista.push({
        id,
        ...g,
        codigo: p?.codigo ?? id.split('_').pop(),
        etiqueta: p
          ? `Parcela ${id}, ${Number.isFinite(p.rendimiento_t_ha) ? `${p.rendimiento_t_ha} ${p.prediction_unit ?? 't/ha'}` : 'rendimiento no disponible'}, ${etiquetasRiesgo[p.riesgo] ?? 'riesgo sin clasificar'}`
          : `Parcela ${id}, sin datos`,
      });
    }
    return lista;
  }, [geometrias, proy, porId, etiquetasRiesgo]);

  const colores = useMemo(() => {
    const m = new Map();
    for (const p of parcelas) {
      if (modo === 'riesgo') {
        if (COLOR_RIESGO[p.riesgo]) m.set(p.id, COLOR_RIESGO[p.riesgo]);
      } else if (Number.isFinite(p.rendimiento_t_ha)) {
        m.set(p.id, colorPorRendimiento(p.rendimiento_t_ha));
      }
    }
    return m;
  }, [parcelas, modo]);

  const conDatos = useMemo(() => items.filter((it) => Number.isFinite(porId.get(it.id)?.rendimiento_t_ha)).length, [items, porId]);
  const sinDatos = items.length - conDatos;

  // Una sola parcela es tabulable (roving tabindex); las flechas mueven la selección
  const tabbableId = items.some((it) => it.id === seleccionadaId) ? seleccionadaId : items[0]?.id;
  const itemSel = items.find((it) => it.id === seleccionadaId);
  const itemHover = hover ? items.find((it) => it.id === hover.id) : null;
  const parcelaHover = hover ? porId.get(hover.id) : null;
  const parcelaSel = porId.get(seleccionadaId);

  // Una sola etiqueta, con tamaño constante en pantalla y fuera del grupo de zoom.
  const escalaBase = proy ? Math.max(Math.min(tamano.w / proy.ancho, tamano.h / proy.alto), 0.001) : 1;
  const seleccionadoX = itemSel ? itemSel.cx * vista.k + vista.x : 0;
  const seleccionadoY = itemSel ? itemSel.cy * vista.k + vista.y : 0;
  const seleccionVisible = itemSel && seleccionadoX >= 0 && seleccionadoX <= proy.ancho
    && seleccionadoY >= 0 && seleccionadoY <= proy.alto;
  const anchoEtiqueta = ((itemSel?.id.length ?? 0) * 7.5 + 24) / escalaBase;
  const etiquetaX = proy ? limitar(seleccionadoX, anchoEtiqueta / 2 + 4 / escalaBase,
    proy.ancho - anchoEtiqueta / 2 - 4 / escalaBase) : 0;
  const etiquetaY = seleccionadoY < 42 / escalaBase ? seleccionadoY + 24 / escalaBase : seleccionadoY - 24 / escalaBase;

  const centrarSeleccion = () => {
    if (!itemSel || !proy) return;
    const k = limitar(Math.min(tamano.w * 0.55 / Math.max(itemSel.ancho * escalaBase, 1),
      tamano.h * 0.55 / Math.max(itemSel.alto * escalaBase, 1)), K_MIN, K_MAX);
    setVista(ajustar({ k, x: proy.ancho / 2 - itemSel.cx * k, y: proy.alto / 2 - itemSel.cy * k }, proy));
    setHover(null);
  };

  // ---------- Zoom ----------
  const zoomEn = useCallback(
    (factor, centro) => {
      const svg = svgRef.current;
      if (!svg || !proy) return;
      const r = svg.getBoundingClientRect();
      const s = Math.min(r.width / proy.ancho, r.height / proy.alto);
      const ox = (r.width - proy.ancho * s) / 2;
      const oy = (r.height - proy.alto * s) / 2;
      const px = centro ? centro.x - r.left : r.width / 2;
      const py = centro ? centro.y - r.top : r.height / 2;
      const cx = (px - ox) / s;
      const cy = (py - oy) / s;
      setVista((v) => {
        const k = limitar(v.k * factor, K_MIN, K_MAX);
        const rel = k / v.k;
        return ajustar({ k, x: cx - (cx - v.x) * rel, y: cy - (cy - v.y) * rel }, proy);
      });
    },
    [proy, svgRef],
  );

  // Ctrl/⌘ + rueda (o pellizco en trackpad) acerca; la rueda sola sigue haciendo scroll de la página
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return undefined;
    const onWheel = (e) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      zoomEn(Math.exp(-limitar(e.deltaY, -50, 50) * 0.01), { x: e.clientX, y: e.clientY });
    };
    svg.addEventListener('wheel', onWheel, { passive: false });
    return () => svg.removeEventListener('wheel', onWheel);
  }, [zoomEn, svgRef]);

  // ---------- Puntero ----------
  const alPresionar = (e) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    arrastre.current = { x: e.clientX, y: e.clientY, vx: vista.x, vy: vista.y };
    movido.current = false;
  };

  const alMover = (e) => {
    const a = arrastre.current;
    if (a && vista.k > 1) {
      const dx = e.clientX - a.x;
      const dy = e.clientY - a.y;
      if (Math.abs(dx) + Math.abs(dy) > 4) movido.current = true;
      if (movido.current && proy) {
        const r = svgRef.current.getBoundingClientRect();
        const s = Math.min(r.width / proy.ancho, r.height / proy.alto);
        setVista((v) => ajustar({ k: v.k, x: a.vx + dx / s, y: a.vy + dy / s }, proy));
        setHover(null);
        return;
      }
    }
    if (e.pointerType === 'touch') return;
    const id = idDe(e.target);
    if (!id) {
      setHover(null);
      return;
    }
    const caja = cajaRef.current.getBoundingClientRect();
    const x = e.clientX - caja.left;
    const y = e.clientY - caja.top;
    setHover({ id, x, y, flip: x > caja.width - 200 });
  };

  const alSoltar = () => {
    arrastre.current = null;
  };

  const alSalir = () => {
    arrastre.current = null;
    setHover(null);
  };

  const alClic = (e) => {
    if (movido.current) {
      movido.current = false; // el clic fue el final de un arrastre
      return;
    }
    const id = idDe(e.target);
    if (id && porId.has(id)) onSelect(id);
  };

  // ---------- Teclado ----------
  const alTeclear = (e) => {
    const id = idDe(e.target);
    if (!id) return;

    if (e.key === ' ') {
      e.preventDefault();
      if (porId.has(id)) onSelect(id);
      return;
    }
    if (e.key === 'Enter') {
      // Si aún no está seleccionada, solo se selecciona: evita que el atajo global
      // de Enter abra la ficha de la parcela anterior.
      if (id !== seleccionadaId && porId.has(id)) {
        e.stopPropagation();
        onSelect(id);
      }
      return;
    }
    const dir = DIRECCIONES[e.key];
    if (dir) {
      e.preventDefault();
      const siguiente = vecinoEn(items, id, dir, porId);
      if (siguiente) {
        onSelect(siguiente);
        svgRef.current
          ?.querySelector(`[data-id="${CSS.escape(siguiente)}"]`)
          ?.focus({ preventScroll: true });
      }
    }
  };

  if (!proy || items.length === 0) return null;

  return (
    <Panel className="flex min-w-0 flex-col p-4 sm:p-6 animate-fade-up">
      {/* Cabecera + selector de color */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-2">
          <p className="section-label">Territorio · exploración interactiva</p>
          <h2 className="section-title">Mapa de parcelas</h2>
          <p className="text-xs text-text-mid">
            <b className="text-text-hi">{parcelas.length}</b> parcelas ·{' '}
            {modo === 'riesgo' ? 'nivel de riesgo' : 'rendimiento esperado'}
          </p>
        </div>
        <div className="flex rounded-lg border border-ink-600 p-0.5 text-sm" role="group" aria-label="Colorear mapa por">
          {[
            ['rendimiento', 'Rendimiento'],
            ['riesgo', 'Riesgo'],
          ].map(([valor, texto]) => (
            <button
              key={valor}
              type="button"
              aria-pressed={modo === valor}
              onClick={() => setModo(valor)}
              className={`rounded-md px-3 py-2 sm:py-1 transition-colors ${
                modo === valor ? 'bg-ink-600 text-text-hi' : 'text-text-mid hover:text-text-hi'
              }`}
            >
              {texto}
            </button>
          ))}
        </div>
      </div>

      {/* Lienzo */}
      <div className="mt-4 flex min-h-[320px] flex-1 flex-col overflow-hidden rounded-xl border border-ink-700/60 bg-ink-950/70 sm:flex-row">
        <div ref={cajaRef} className="relative min-h-[300px] flex-1">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${proy.ancho.toFixed(1)} ${proy.alto.toFixed(1)}`}
          preserveAspectRatio="xMidYMid meet"
          role="group"
          aria-label="Mapa de parcelas. Usa las flechas para moverte entre parcelas y Espacio para seleccionar."
          className="absolute inset-0 h-full w-full select-none"
          style={{ touchAction: vista.k > 1 ? 'none' : 'pan-y pinch-zoom' }}
          onPointerDown={alPresionar}
          onPointerMove={alMover}
          onPointerUp={alSoltar}
          onPointerCancel={alSalir}
          onPointerLeave={alSalir}
          onClick={alClic}
          onKeyDown={alTeclear}
        >
          <g transform={`translate(${vista.x} ${vista.y}) scale(${vista.k})`}>
            <CapaParcelas
              items={items}
              colores={colores}
              tabbableId={tabbableId}
              seleccionadaId={seleccionadaId}
            />

            {/* Resaltes encima de todo para que ningún vecino tape el borde */}
            {itemHover && itemHover.id !== seleccionadaId && (
              <path
                d={itemHover.d}
                fill="none"
                stroke="#ffffff"
                strokeOpacity="0.75"
                strokeWidth="1.5"
                vectorEffect="non-scaling-stroke"
                pointerEvents="none"
              />
            )}
            {itemSel && (
              <path
                d={itemSel.d}
                fill="none"
                stroke="#ffffff"
                strokeWidth="2.5"
                strokeLinejoin="round"
                vectorEffect="non-scaling-stroke"
                pointerEvents="none"
              />
            )}

          </g>
          {seleccionVisible && (
            <g pointerEvents="none" aria-hidden="true" data-selected-label={itemSel.id}>
              <circle cx={seleccionadoX} cy={seleccionadoY} r={8 / escalaBase}
                fill="none" stroke="#d8e7dc" strokeWidth={1 / escalaBase} strokeOpacity="0.8" />
              <line x1={seleccionadoX} y1={seleccionadoY} x2={etiquetaX} y2={etiquetaY}
                stroke="#d8e7dc" strokeWidth={1 / escalaBase} strokeOpacity="0.6" />
              <rect x={etiquetaX - anchoEtiqueta / 2} y={etiquetaY - 13 / escalaBase}
                width={anchoEtiqueta} height={26 / escalaBase} rx={6 / escalaBase}
                fill="#172a20" stroke="#d8e7dc" strokeWidth={1 / escalaBase} />
              <text x={etiquetaX} y={etiquetaY} fill="#f2f7f3" fontSize={12 / escalaBase}
                fontWeight="600" textAnchor="middle" dominantBaseline="central">{itemSel.id}</text>
            </g>
          )}
        </svg>

        <div className="pointer-events-none absolute left-3 top-3 rounded-md border border-ink-600 bg-ink-950/90 px-2 py-1 text-[11px] text-text-mid">
          {vista.k === 1 ? 'Vista general' : `Zoom ${vista.k.toFixed(1)}×`} · {sintetica ? 'geometría de ejemplo' : 'contornos reales'}
        </div>

        {/* Tooltip (solo mouse/lápiz) */}
        {hover && (
          <div
            role="tooltip"
            className="pointer-events-none absolute z-20 whitespace-nowrap rounded-lg border border-ink-600
                       bg-ink-950/95 px-3 py-2 text-sm shadow-panel"
            style={{
              left: hover.x,
              top: hover.y,
              transform: `translate(${hover.flip ? 'calc(-100% - 12px)' : '12px'}, 12px)`,
            }}
          >
            <div className="font-semibold text-text-hi">
              {hover.id}
              {parcelaHover?.municipio ? (
                <span className="font-normal text-text-mid"> · {parcelaHover.municipio}</span>
              ) : null}
            </div>
            {parcelaHover ? (
              <div className="mt-0.5 text-text-mid">
                {Number.isFinite(parcelaHover.rendimiento_t_ha) ? `${parcelaHover.rendimiento_t_ha.toFixed(4)} ${parcelaHover.prediction_unit ?? 't/ha'}` : 'Rendimiento no disponible'} ·{' '}
                {etiquetasRiesgo[parcelaHover.riesgo] ?? 'riesgo sin clasificar'}
              </div>
            ) : (
              <div className="mt-0.5 text-text-lo">Sin datos de rendimiento</div>
            )}
          </div>
        )}
        </div>

        {/* Controles de zoom: barra propia (inferior en móvil, lateral en pantallas anchas) */}
        <div className="flex justify-end gap-1.5 border-t border-ink-700/60 p-1.5 sm:flex-col sm:justify-start sm:border-l sm:border-t-0">
          <BotonControl etiqueta="Acercar" onClick={() => zoomEn(1.5)} disabled={vista.k >= K_MAX}>
            +
          </BotonControl>
          <BotonControl etiqueta="Alejar" onClick={() => zoomEn(1 / 1.5)} disabled={vista.k <= K_MIN}>
            −
          </BotonControl>
          <BotonControl etiqueta="Centrar parcela seleccionada" onClick={centrarSeleccion} disabled={!itemSel}>
            ◎
          </BotonControl>
          <BotonControl
            etiqueta="Restablecer vista"
            onClick={() => setVista(VISTA_INICIAL)}
            disabled={vista.k === 1 && vista.x === 0 && vista.y === 0}
          >
            ⟲
          </BotonControl>
        </div>
      </div>

      {/* Selección actual: en móvil/tablet la ficha queda debajo del mapa, así que se
          resume aquí con un acceso directo (en escritorio ya está a la derecha) */}
      {parcelaSel && onAbrir && (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-moss-700/40 bg-moss-900/30 px-4 py-3 lg:hidden">
          <div className="min-w-0 text-sm">
            <div className="truncate font-semibold text-text-hi">{parcelaSel.id}</div>
            <div className="text-text-mid">
              {Number.isFinite(parcelaSel.rendimiento_t_ha) ? `${parcelaSel.rendimiento_t_ha.toFixed(4)} ${parcelaSel.prediction_unit ?? 't/ha'}` : 'Rendimiento no disponible'} ·{' '}
              {etiquetasRiesgo[parcelaSel.riesgo] ?? 'riesgo sin clasificar'}
            </div>
          </div>
          <button
            type="button"
            onClick={onAbrir}
            className="shrink-0 rounded-lg border border-moss-700/50 bg-moss-900 px-4 py-2.5 text-sm
                       font-semibold text-moss-500 transition-colors hover:bg-moss-700 hover:text-white"
          >
            Abrir ficha
          </button>
        </div>
      )}

      {/* Leyenda y ayuda */}
      <div className="mt-auto space-y-2 pt-5">
        {modo === 'riesgo' ? (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-text-mid">
            {Object.entries(COLOR_RIESGO).map(([nivel, color]) => (
              <span key={nivel} className="inline-flex items-center gap-1.5">
                <span className="h-3 w-5 rounded-sm" style={{ backgroundColor: color }} />
                {etiquetasRiesgo[nivel]}
              </span>
            ))}
            <span className="inline-flex items-center gap-1.5"><span className="h-3 w-5 rounded-sm border border-[#82958a]" style={{ backgroundColor: SIN_DATO }} aria-hidden="true" />Sin riesgo disponible</span>
          </div>
        ) : (
          <LeyendaRendimiento />
        )}
        {sinDatos > 0 && modo === 'rendimiento' && (
          <p className="text-sm text-text-lo">
            {sinDatos} {sinDatos === 1 ? 'parcela sin resultado cargado' : 'parcelas sin resultado cargado'} en esta vista. Selecciona una para consultar su estimación.
          </p>
        )}
        <p className="text-sm text-text-lo">
          Selecciona una parcela para ver su etiqueta y consultar su estimación. Usa ◎ para centrarla.{' '}
          <span className="[@media(hover:none)]:hidden">Ctrl + rueda para acercar, o usa los botones.</span>
          <span className="hidden [@media(hover:none)]:inline">Usa + y − para acercar.</span>
        </p>
        {sintetica && (
          <p className="text-sm text-amber-400/90">
            Geometrías de ejemplo: las formas son ilustrativas, no las parcelas reales.
          </p>
        )}
      </div>
    </Panel>
  );
}
