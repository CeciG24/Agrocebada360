import { esFeatureCollectionValida } from '../lib/geo';

// Carga opcional de un archivo local SOLO para la demostración.
// En modo API, ApiRepository obtiene geometrías de /parcels?include_geometry=true.
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
