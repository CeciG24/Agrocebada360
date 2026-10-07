const num = (v, fallback = 0) => (typeof v === 'number' && Number.isFinite(v) ? v : fallback);

export const fmtT    = (v) => `${num(v).toFixed(2)} t/ha`;
export const fmtHa   = (v) => `${num(v).toFixed(1)} ha`;
export const fmtTons = (v) => `${num(v).toFixed(1)} t`;
export const fmtPct  = (v) => `${Math.round(num(v))}%`;
export const fmtSigned = (v) => {
  const n = num(v);
  return n >= 0 ? `+${n.toFixed(2)}` : n.toFixed(2);
};