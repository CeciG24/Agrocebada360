// ============================================================
// Geometrías SINTÉTICAS para el modo demo.
// Sirven mientras no exista public/data/parcelas.geojson (ver
// scripts/shp-to-geojson.mjs). Generan un mosaico de parcelas contiguas
// (comparten vértices, como en un parcelario real) a partir de los ids,
// de forma determinista: el mismo id siempre cae en el mismo lugar.
// ============================================================

// PRNG determinista (mulberry32)
function mulberry32(semilla) {
  let a = semilla;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const r5 = (n) => Math.round(n * 1e5) / 1e5;

export function generarGeometriasMock(
  ids,
  { lon0 = -98.12, lat0 = 19.62, lado = 260 } = {}, // ~Tlaxco, Tlaxcala; lado en metros
) {
  const n = ids.length;
  const cols = Math.max(1, Math.ceil(Math.sqrt(n * 1.6)));
  const filas = Math.max(1, Math.ceil(n / cols));
  const rand = mulberry32(360);

  const gradosLat = 1 / 111320;
  const gradosLon = 1 / (111320 * Math.cos((lat0 * Math.PI) / 180));

  // Retícula de vértices con ruido: las parcelas vecinas comparten aristas.
  const vertices = [];
  for (let j = 0; j <= filas; j++) {
    const fila = [];
    for (let i = 0; i <= cols; i++) {
      const ruidoX = (rand() - 0.5) * 0.5 * lado;
      const ruidoY = (rand() - 0.5) * 0.5 * lado;
      fila.push([
        r5(lon0 + (i * lado + ruidoX) * gradosLon),
        r5(lat0 - (j * lado + ruidoY) * gradosLat),
      ]);
    }
    vertices.push(fila);
  }

  const features = ids.map((id, idx) => {
    const i = idx % cols;
    const j = Math.floor(idx / cols);
    const anillo = [
      vertices[j][i],
      vertices[j][i + 1],
      vertices[j + 1][i + 1],
      vertices[j + 1][i],
      vertices[j][i],
    ];
    return {
      type: 'Feature',
      properties: { id },
      geometry: { type: 'Polygon', coordinates: [anillo] },
    };
  });

  return { type: 'FeatureCollection', properties: { sintetica: true }, features };
}
