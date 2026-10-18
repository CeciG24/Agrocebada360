// ============================================================
// Utilidades geográficas: dibujan polígonos GeoJSON (WGS84) como SVG.
// No usa tiles ni internet, así que funciona igual en modo demo offline.
// ============================================================

const LADO = 1000;  // unidades SVG del lado mayor del mapa
const MARGEN = 16;  // aire alrededor, en unidades SVG

const esFinito = (n) => Number.isFinite(n);

export function esGeometriaValida(geometry) {
  if (geometry === null) return true;
  if (!geometry || !['Polygon', 'MultiPolygon'].includes(geometry.type) || !Array.isArray(geometry.coordinates)) return false;
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  return polygons.length > 0 && polygons.every((rings) => Array.isArray(rings) && rings.length > 0 && rings.every((ring) =>
    Array.isArray(ring) && ring.length >= 4 && ring.every((point) =>
      Array.isArray(point) && point.length >= 2 && point.every(esFinito) && Math.abs(point[0]) <= 180 && Math.abs(point[1]) <= 90)
    && ring[0][0] === ring.at(-1)[0] && ring[0][1] === ring.at(-1)[1]));
}

/** Devuelve siempre una lista de polígonos (cada uno es una lista de anillos). */
export function poligonosDe(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'Polygon') return [geometry.coordinates];
  if (geometry.type === 'MultiPolygon') return geometry.coordinates;
  return [];
}

export function esFeatureCollectionValida(fc) {
  return Boolean(fc) && fc.type === 'FeatureCollection' && Array.isArray(fc.features);
}

/**
 * Proyección equirrectangular con corrección por latitud (cos φ).
 * En un área del tamaño de una región agrícola la distorsión es despreciable
 * y las parcelas conservan su forma. Normaliza a un lienzo de ~1000 unidades.
 */
export function construirProyeccion(features) {
  let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;

  for (const f of features) {
    for (const poligono of poligonosDe(f?.geometry)) {
      for (const anillo of poligono) {
        for (const [lon, lat] of anillo) {
          if (!esFinito(lon) || !esFinito(lat)) continue;
          if (lon < minLon) minLon = lon;
          if (lon > maxLon) maxLon = lon;
          if (lat < minLat) minLat = lat;
          if (lat > maxLat) maxLat = lat;
        }
      }
    }
  }
  if (!esFinito(minLon)) return null; // no hay ni un punto válido

  const kx = Math.cos((((minLat + maxLat) / 2) * Math.PI) / 180);
  const w = (maxLon - minLon) * kx;
  const h = maxLat - minLat;
  const escala = LADO / (Math.max(w, h) || 1e-9);

  return {
    proyectar: (lon, lat) => [
      (lon - minLon) * kx * escala + MARGEN,
      (maxLat - lat) * escala + MARGEN,
    ],
    ancho: w * escala + 2 * MARGEN,
    alto: h * escala + 2 * MARGEN,
  };
}

/**
 * Convierte una geometría en un `d` de <path> y calcula el centro de su caja.
 * Devuelve null si la geometría no tiene puntos válidos.
 */
export function procesarGeometria(geometry, proyectar) {
  let d = '';
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

  for (const poligono of poligonosDe(geometry)) {
    for (const anillo of poligono) {
      let primero = true;
      for (const [lon, lat] of anillo) {
        if (!esFinito(lon) || !esFinito(lat)) continue;
        const [x, y] = proyectar(lon, lat);
        d += `${primero ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`;
        primero = false;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
      if (!primero) d += 'Z';
    }
  }
  if (!d) return null;
  return { d, cx: (minX + maxX) / 2, cy: (minY + maxY) / 2, ancho: maxX - minX, alto: maxY - minY };
}
