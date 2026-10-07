import { colorPorRendimiento } from '../../lib/colores';

// ---------- Hash determinista por ID ----------
function hashId(id) {
  let h = 0;
  for (let i = 0; i < id.length; i++) {
    h = (h * 31 + id.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

// ---------- Genera rotación, offset y clip-path únicos ----------
function shapeFor(id) {
  const h = hashId(id);

  // Rotación entre -2.2° y +2.2°
  const rot = ((h % 9) - 4) * 0.55;

  // Desplazamiento vertical entre -4 y +4 px
  const offsetY = ((h >> 4) % 9) - 4;

  // 8 valores pseudoaleatorios entre -4 y +4 para las esquinas
  const n = [];
  let x = h;
  for (let i = 0; i < 8; i++) {
    x = (x * 1103515245 + 12345) | 0;
    n.push((Math.abs(x) % 9) - 4);
  }

  // Cuadrilátero: TL, TR, BR, BL
  const clip = `polygon(
    ${3 + n[0]}% ${5 + n[1]}%,
    ${97 + n[2]}% ${3 + n[3]}%,
    ${96 + n[4]}% ${95 + n[5]}%,
    ${4 + n[6]}% ${97 + n[7]}%
  )`;

  return { rot, offsetY, clip };
}

export function ParcelaTile({ parcela, seleccionada, onClick }) {
  const bg = colorPorRendimiento(parcela.rendimiento_t_ha);
  const { rot, offsetY, clip } = shapeFor(parcela.id);

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Parcela ${parcela.id}`}
      className="group relative aspect-[5/4] transition-transform duration-200 hover:z-10"
      style={{
        transform: `rotate(${rot}deg) translateY(${offsetY}px)`,
      }}
    >
      {/* Aura blanca cuando está seleccionada */}
      {seleccionada && (
        <span
          aria-hidden
          className="absolute inset-0 bg-white"
          style={{
            clipPath: clip,
            transform: 'scale(1.14)',
          }}
        />
      )}

      {/* Sombra sutil detrás del tile (da profundidad) */}
      <span
        aria-hidden
        className="absolute inset-0 bg-black/50"
        style={{
          clipPath: clip,
          transform: 'translate(2px, 3px) scale(1.02)',
        }}
      />

      {/* Tile coloreado */}
      <span
        className="absolute inset-0 grid place-items-center
                   transition-[filter] duration-200
                   group-hover:brightness-125
                   group-active:brightness-90"
        style={{ backgroundColor: bg, clipPath: clip }}
      >
        <span className="text-sm font-semibold text-white/95 tracking-wide drop-shadow-sm">
          {parcela.codigo}
        </span>
      </span>
    </button>
  );
}