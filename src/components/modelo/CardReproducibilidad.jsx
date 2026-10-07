import { useState } from 'react';

export function CardReproducibilidad() {
  const [copiado, setCopiado] = useState(false);
  const comando = 'python -m cebada360.predict --model artifacts/modelo_oficial.pkl --input data/eval.csv --output nombre_del_equipo_prediccion.csv';

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(comando);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      /* silencioso */
    }
  };

  return (
    <div className="rounded-2xl border border-ink-700/60 bg-ink-900/70 p-6 animate-fade-up">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="text-base font-semibold text-text-hi">
            Reproducibilidad
          </h3>
          <p className="mt-1 text-sm text-text-mid">
            El CSV oficial de predicciones se genera desde este pipeline, sin edición manual.
          </p>
        </div>
        <span className="rounded-full bg-moss-900/60 border border-moss-700/40 px-3 py-1
                         text-xs font-semibold text-moss-500 whitespace-nowrap">
          v0.1 · congelado
        </span>
      </div>

      {/* Comando */}
      <div className="rounded-xl bg-ink-950 border border-ink-700/60 p-3 relative group">
        <pre className="text-xs text-text-mid whitespace-pre-wrap break-all pr-20 font-mono leading-relaxed">
          {comando}
        </pre>
        <button
          type="button"
          onClick={copiar}
          className="absolute top-2 right-2 rounded-md border border-ink-600/60
                     bg-ink-800/90 px-2.5 py-1 text-xs text-text-mid
                     hover:border-moss-700/50 hover:text-moss-500
                     transition-colors duration-150"
        >
          {copiado ? 'Copiado' : 'Copiar'}
        </button>
      </div>

      {/* Metadata */}
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
        <div className="rounded-lg bg-ink-800/50 px-3 py-2">
          <div className="text-text-lo">Modelo</div>
          <div className="text-text-hi mt-0.5">Gradient Boosting</div>
        </div>
        <div className="rounded-lg bg-ink-800/50 px-3 py-2">
          <div className="text-text-lo">Features</div>
          <div className="text-text-hi mt-0.5">34 · multisensor + clima + topo</div>
        </div>
        <div className="rounded-lg bg-ink-800/50 px-3 py-2">
          <div className="text-text-lo">Entrenado</div>
          <div className="text-text-hi mt-0.5">2025-09-28</div>
        </div>
      </div>

      {/* Links */}
      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        <a
          href="#"
          className="inline-flex items-center gap-2 text-moss-500 hover:text-moss-400 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Repositorio
        </a>
        <a
          href="#"
          className="inline-flex items-center gap-2 text-moss-500 hover:text-moss-400 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
            <path d="M14 2v6h6M9 13h6M9 17h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          Metodología completa
        </a>
      </div>
    </div>
  );
}