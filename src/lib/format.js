export const esNum = (v) => typeof v === 'number' && Number.isFinite(v);

// Si el valor falta o no es un número válido se muestra '—' (nunca 0).
export const fmtNum = (v, d = 2) => (esNum(v) ? v.toFixed(d) : '—');

export const fmtT    = (v) => (esNum(v) ? `${v.toFixed(2)} t/ha` : '—');
export const fmtHa   = (v) => (esNum(v) ? `${v.toFixed(1)} ha` : '—');
export const fmtTons = (v) => (esNum(v) ? `${v.toFixed(1)} t` : '—');
export const fmtPct  = (v) => (esNum(v) ? `${Math.round(v)}%` : '—');
export const fmtSigned = (v) => {
  if (!esNum(v)) return '—';
  return v >= 0 ? `+${v.toFixed(2)}` : v.toFixed(2);
};