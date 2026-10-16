import { useEffect, useRef } from 'react';
import { useDemoStore } from '../../store/demoStore';

export function ModoListener() {
  const modoDemo = useDemoStore((s) => s.modoDemo);
  const anterior = useRef(modoDemo);

  useEffect(() => {
    if (anterior.current !== modoDemo) {
      // Cambió el modo: recargamos para que todo vuelva a consultar
      window.location.reload();
    }
    anterior.current = modoDemo;
  }, [modoDemo]);

  return null;
}