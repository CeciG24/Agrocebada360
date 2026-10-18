// Verde más intenso = mayor rendimiento. Escala discreta para tiles.
export const COLOR_SIN_RESULTADO = '#33443c';

export function colorPorRendimiento(t) {
  if (t >= 5.0) return '#16a34a';   // moss-600
  if (t >= 4.5) return '#15803d';   // moss-700
  if (t >= 4.0) return '#166534';
  if (t >= 3.5) return '#14532d';
  return '#0f2a1a';
}

export const riesgoColor = {
  bajo:  { dot: 'bg-risk-low',  bg: 'bg-moss-900', text: 'text-moss-500', border: 'border-moss-700/40' },
  medio: { dot: 'bg-risk-mid',  bg: 'bg-amber-950/40', text: 'text-amber-400', border: 'border-amber-700/40' },
  alto:  { dot: 'bg-risk-high', bg: 'bg-rose-950/40', text: 'text-rose-400',  border: 'border-rose-700/40' },
};
