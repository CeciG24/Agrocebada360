import { riesgoColor } from '../../lib/colores';

const LABEL = { bajo: 'Riesgo\nbajo', medio: 'Riesgo\nmedio', alto: 'Riesgo\nalto' };

export function RiskBadge({ nivel }) {
  const c = riesgoColor[nivel] ?? riesgoColor.bajo;
  return (
    <span
      key={nivel}
      className={`inline-block rounded-lg px-3.5 py-2 text-sm font-semibold uppercase tracking-wide
                  ${c.bg} ${c.text} border ${c.border}
                  whitespace-pre-line leading-tight text-right
                  animate-pop-in`}
    >
      {LABEL[nivel]}
    </span>
  );
}