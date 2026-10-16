import { esFeatureCollectionValida } from '../lib/geo';

// Las geometrías de las parcelas son estáticas (no cambian entre consultas),
// así que se sirven como archivo y no dependen del backend ni de su contrato.
// Se generan con: node scripts/shp-to-geojson.mjs <parcelas.shp>
export async function cargarGeometriasEstaticas() {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/parcelas.geojson`);
    if (!res.ok) return null;
    // En dev, Vite responde index.html (200) si el archivo no existe: el
    // .json() lanza y caemos al catch, igual que con una respuesta corrupta.
    const fc = await res.json();
    return esFeatureCollectionValida(fc) && fc.features.length > 0 ? fc : null;
  } catch {
    return null;
  }
}
