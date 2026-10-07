export function FactoresLimitantes({ municipios }) {
  // Cuenta frecuencia de cada factor
  const conteo = new Map();
  municipios.forEach((m) => {
    (m.factores_limitantes ?? []).forEach((f) => {
      conteo.set(f, (conteo.get(f) ?? 0) + 1);
    });
  });

  const lista = [...conteo.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  if (lista.length === 0) {
    return (
      <div className="text-sm text-text-lo">
        Sin factores limitantes registrados.
      </div>
    );
  }

  const max = lista[0][1];

  return (
    <div>
      <div className="text-base text-text-mid mb-3">
        Factores limitantes predominantes en la región
      </div>
      <div className="flex flex-wrap gap-2">
        {lista.map(([factor, n], idx) => {
          const peso = n / max; // 0..1
          return (
            <span
              key={factor}
              className="rounded-full border px-3 py-1.5 text-sm animate-fade-up"
              style={{
                animationDelay: `${idx * 50}ms`,
                borderColor: `rgba(34, 197, 94, ${0.15 + peso * 0.35})`,
                backgroundColor: `rgba(15, 42, 26, ${0.4 + peso * 0.4})`,
                color: peso > 0.5 ? '#22c55e' : '#a3b0aa',
                fontWeight: peso > 0.7 ? 600 : 500,
              }}
            >
              {factor}
              <span className="ml-2 text-xs opacity-60">{n}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}