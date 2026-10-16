import { useEffect, useRef, useState } from 'react';

// Tamaño real (en píxeles) de un elemento SVG, para que el texto mantenga un
// tamaño legible sin importar el zoom ni el ancho de pantalla.
export function useTamanoPx(activo = true) {
  const ref = useRef(null);
  const [tam, setTam] = useState({ w: 600, h: 300 });
  useEffect(() => {
    const el = ref.current;
    if (!activo || !el || typeof ResizeObserver === 'undefined') return undefined;
    const ro = new ResizeObserver(([entry]) =>
      setTam({ w: entry.contentRect.width, h: entry.contentRect.height }),
    );
    ro.observe(el);
    return () => ro.disconnect();
  }, [activo]);
  return [ref, tam];
}