import { ChartPlaceholder } from '../common/ChartPlaceholder';
import { esNum } from '../../lib/format';
import { regionLabel } from '../../lib/regions';

export function RegionComparison({ items, selected }) {
  // Solo se comparan valores que comparten unidad y versión de modelo.
  const comparable = selected && selected.predicted_count > 0
    ? items.filter((item) => item.predicted_count > 0 && esNum(item.mean_prediction)
      && item.unit === selected.unit && item.model_version === selected.model_version) : [];
  if (comparable.length === 0) return <ChartPlaceholder title="La comparación regional está preparada" description="Aparecerá cuando existan medias regionales con unidad y versión compatibles." xLabel="Rendimiento medio" yLabel="Regiones" />;
  const limit = Math.max(...comparable.map((item) => Math.abs(item.mean_prediction)), 0.001);
  return (
    <div>
      <p className="mb-5 text-xs text-text-mid">Modelo {selected.model_version} · {selected.unit} · media por parcela</p>
      <ul className="space-y-4" aria-label="Comparación del rendimiento medio por región">
        {comparable.map((item) => (
          <li key={item.region} className="grid grid-cols-[minmax(75px,1fr)_minmax(60px,2fr)_auto] items-center gap-3">
            <span className={`break-words text-xs ${item.region === selected.region ? 'font-semibold text-text-hi' : 'text-text-mid'}`}>{regionLabel(item.region)}</span>
            <div className="h-7 overflow-hidden rounded-md bg-ink-800" aria-hidden="true"><div className={`h-full rounded-md ${item.mean_prediction < 0 ? 'bg-rose-400/60' : item.region === selected.region ? 'bg-moss-500' : 'bg-moss-700/60'}`} style={{ width: `${Math.abs(item.mean_prediction) / limit * 100}%` }} /></div>
            <span className="text-xs tabular-nums text-text-hi">{item.mean_prediction.toFixed(4)} <span className="text-text-mid">{item.unit}</span></span>
          </li>
        ))}
      </ul>
      <p className="mt-5 text-xs text-text-mid">La longitud representa la magnitud; el valor conserva su signo. La cobertura de cada región se muestra en la tabla.</p>
    </div>
  );
}
