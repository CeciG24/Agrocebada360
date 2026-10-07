const CORTES = [
  { id: 'junio',        label: 'Junio' },
  { id: 'julio-agosto', label: 'Jul-Ago' },
  { id: 'septiembre',   label: 'Septiembre' },
  { id: 'octubre',      label: 'Octubre' },
];

export function SelectorCorte({ valor, onChange }) {
  return (
    <div className="inline-flex rounded-xl border border-ink-700/60 bg-ink-800/70 p-1">
      {CORTES.map((c) => {
        const activo = c.id === valor;
        return (
          <button
            key={c.id}
            type="button"
            onClick={() => onChange(c.id)}
            className={`px-3 py-1.5 text-sm rounded-lg transition ${
              activo
                ? 'bg-moss-900 text-moss-500 font-semibold border border-moss-700/40'
                : 'text-text-mid hover:text-text-hi'
            }`}
          >
            {c.label}
          </button>
        );
      })}
    </div>
  );
}