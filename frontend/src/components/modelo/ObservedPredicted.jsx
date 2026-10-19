import { ChartPlaceholder } from '../common/ChartPlaceholder';

export function ObservedPredicted({ oof }) {
  const points = oof?.points ?? [];
  if (!points.length) return <ChartPlaceholder title="Comparación de predicciones" description="No hay pares fuera de muestra disponibles para esta gráfica." xLabel="Rendimiento observado" yLabel="Rendimiento predicho" />;
  const lo = Math.floor(Math.min(0, ...points.flatMap((p) => [p.observed, p.predicted])));
  const hi = Math.ceil(Math.max(1, ...points.flatMap((p) => [p.observed, p.predicted])));
  const x = (value) => 65 + (value - lo) / (hi - lo) * 495;
  const y = (value) => 325 - (value - lo) / (hi - lo) * 290;
  const ticks = Array.from({ length: 6 }, (_, i) => lo + (hi - lo) * i / 5);
  return <div className="min-w-0 space-y-3">
    <svg viewBox="0 0 600 390" className="w-full" role="img" aria-label={`Observado frente a predicho: ${points.length} parcelas con predicciones fuera de fold. La línea discontinua indica coincidencia exacta.`}>
      {ticks.map((tick) => <g key={tick}>
        <path d={`M${x(tick)},35 V325 M65,${y(tick)} H560`} stroke="#26392e" strokeWidth="1" />
        <text x={x(tick)} y="346" textAnchor="middle" fill="#a9b6ae" fontSize="13">{tick.toFixed(1)}</text>
        <text x="54" y={y(tick) + 4} textAnchor="end" fill="#a9b6ae" fontSize="13">{tick.toFixed(1)}</text>
      </g>)}
      <path d="M65,325 L560,35" stroke="#b4c7bb" strokeWidth="1.5" strokeDasharray="6 5" />
      {points.map((p) => <circle key={p.parcel_id} cx={x(p.observed)} cy={y(p.predicted)} r="4" fill="#20c66a" fillOpacity="0.65" stroke="#83e5ab" strokeWidth="0.6"><title>{p.parcel_id}: observado {p.observed.toFixed(4)}, predicho OOF {p.predicted.toFixed(4)} t/ha</title></circle>)}
      <text x="310" y="378" textAnchor="middle" fill="#c5d2ca" fontSize="14">Rendimiento observado (t/ha)</text>
      <text transform="translate(18 180) rotate(-90)" textAnchor="middle" fill="#c5d2ca" fontSize="14">Rendimiento predicho (t/ha)</text>
    </svg>
    <p className="text-xs leading-relaxed text-text-mid">{points.length} parcelas etiquetadas. {oof.method} La línea representa observado = predicho.</p>
    <p className="text-xs leading-relaxed text-text-mid">{oof.note}</p>
    <details className="rounded-lg border border-ink-700 p-3 text-xs text-text-mid"><summary className="cursor-pointer">Consultar los {points.length} pares fuera de muestra</summary><div className="mt-3 max-h-64 overflow-auto"><table className="w-full text-left tabular-nums"><caption className="sr-only">Valores OOF, no predicciones ajustadas sobre entrenamiento</caption><thead><tr><th className="p-2">Parcela</th><th className="p-2">Observado</th><th className="p-2">Predicho</th></tr></thead><tbody>{points.map((p) => <tr key={p.parcel_id}><th scope="row" className="p-2 font-normal">{p.parcel_id}</th><td className="p-2">{p.observed.toFixed(4)}</td><td className="p-2">{p.predicted.toFixed(4)}</td></tr>)}</tbody></table></div></details>
  </div>;
}
