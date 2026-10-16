// Estado vacío reutilizable: "no hay nada que mostrar" explicado, nunca un hueco en blanco.
export function EmptyState({ titulo, detalle, children }) {
  return (
    <div className="flex flex-col items-center gap-3 px-4 py-10 text-center">
      <div className="grid h-11 w-11 place-items-center rounded-full border border-ink-600 bg-ink-800/70 text-text-lo">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M4 13h4l1.5 3h5L16 13h4M4 13l2.2-7.2A2 2 0 0 1 8.1 4.4h7.8a2 2 0 0 1 1.9 1.4L20 13M4 13v5a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"
            stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"
          />
        </svg>
      </div>
      <div className="text-base font-medium text-text-hi">{titulo}</div>
      {detalle && <p className="max-w-sm text-sm text-text-lo">{detalle}</p>}
      {children}
    </div>
  );
}
