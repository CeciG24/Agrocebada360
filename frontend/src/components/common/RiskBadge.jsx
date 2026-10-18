import { riesgoColor } from '../../lib/colores';

const LABEL = { bajo: 'Riesgo\nbajo', medio: 'Riesgo\nmedio', alto: 'Riesgo\nalto' };

export function RiskBadge({ nivel, revision = false }) {
  const labels = revision ? { bajo: 'Sin alerta\ncombinada', medio: 'Revisión\nmedia', alto: 'Prioridad\nalta' } : LABEL;
  if (!LABEL[nivel]) {
    return (
      <span className="inline-block rounded-lg px-3.5 py-2 text-sm font-semibold uppercase tracking-wide
                       bg-ink-800 text-text-lo border border-ink-600
                       whitespace-pre-line leading-tight text-right">
        {'Riesgo\nno disponible'}
      </span>
    );
  }
  const c = riesgoColor[nivel];
  return (
    <span
      key={nivel}
      className={`inline-block rounded-lg px-3.5 py-2 text-sm font-semibold uppercase tracking-wide
                  ${c.bg} ${c.text} border ${c.border}
                  whitespace-pre-line leading-tight text-right
                  animate-pop-in`}
    >
      {labels[nivel]}
    </span>
  );
}
