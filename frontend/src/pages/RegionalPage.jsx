import { useEffect, useState } from 'react';
import { Panel } from '../components/common/Panel';
import { WorkspaceHeader } from '../components/common/WorkspaceHeader';
import { StatCard } from '../components/common/StatCard';
import { PendingState } from '../components/common/PendingState';
import { RegionComparison } from '../components/regional/RegionComparison';
import { repo } from '../data';
import { fmtNum } from '../lib/format';
import { regionDefinition, regionDefinitionVersion, regionLabel } from '../lib/regions';

export function RegionalPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selectedKey, setSelectedKey] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  useEffect(() => {
    let alive = true;
    repo.getRegionResumen().then((value) => alive && setData(value)).catch((e) => alive && setError(e.message));
    return () => { alive = false; };
  }, []);
  const allItems = data?.items ?? [];
  const allUnavailable = data?.unavailable ?? [];
  const states = [...new Set([...allItems, ...allUnavailable].map((item) => regionDefinition(item.region)?.state).filter(Boolean))].sort();
  const items = allItems.filter((item) => !stateFilter || regionDefinition(item.region)?.state === stateFilter);
  const unavailable = allUnavailable.filter((item) => !stateFilter || regionDefinition(item.region)?.state === stateFilter);
  const keys = [...new Set([...items.map((item) => item.region), ...unavailable.map((item) => item.region)])];
  const key = keys.includes(selectedKey) ? selectedKey : keys[0] ?? '';
  const selected = items.find((item) => item.region === key);
  const loading = !data && !error;
  const isReal = data?.meta?.mode === 'real';
  const definition = regionDefinition(key);
  return (
    <div className="workspace">
      <WorkspaceHeader eyebrow="Perspectiva territorial" title="Del territorio al contexto."
        description="Compara regiones con resultados compatibles y revisa cuántas parcelas respaldan cada lectura.">
        <div className="flex max-w-full flex-wrap gap-3">
          {states.length > 0 && <div><label htmlFor="state-select" className="mb-2 block text-xs text-text-mid">Estado</label><select id="state-select" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} className="min-h-11 max-w-full rounded-xl border border-ink-600 bg-ink-900 px-4 text-sm text-text-hi"><option value="">Todos los estados</option>{states.map((state) => <option key={state} value={state}>{state}</option>)}</select></div>}
          {keys.length > 0 && <div className="min-w-0"><label htmlFor="region-select" className="mb-2 block text-xs text-text-mid">Región seleccionada</label><select id="region-select" value={key} onChange={(e) => setSelectedKey(e.target.value)} className="min-h-11 max-w-full rounded-xl border border-ink-600 bg-ink-900 px-4 text-sm text-text-hi">{keys.map((r) => <option key={r} value={r}>{regionLabel(r)}</option>)}</select></div>}
        </div>
      </WorkspaceHeader>
      {isReal && <p className="text-sm leading-relaxed text-text-mid">Resumen de las parcelas del dataset por regiones de referencia estatal. La media usa únicamente las predicciones de evaluación; no representa a todos los productores de la región ni incluye rendimientos observados de entrenamiento.</p>}
      {isReal && selected?.predicted_count > 0 && selected.predicted_count < 5 && <p role="status" className="rounded-xl border border-amber-800/40 bg-amber-950/20 p-4 text-sm text-amber-200">Muestra pequeña: {regionLabel(key)} tiene {selected.predicted_count} predicciones de evaluación. Interpreta la media junto con su cobertura.</p>}
      {error && <p role="alert" className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-200">No se pudo consultar la información regional: {error}</p>}
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-5" aria-label="Indicadores de la región seleccionada">
        <StatCard label="Rendimiento medio" value={selected?.predicted_count > 0 ? fmtNum(selected.mean_prediction, 4) : null} unit={selected?.unit} note="Media por parcela, sin ponderar por área" loading={loading} accent />
        <StatCard label="Cobertura predictiva" value={selected ? `${selected.predicted_count} / ${selected.parcel_count}` : null} note="Parcelas con predicción / total de la región" loading={loading} />
        <StatCard label="Parcelas" value={selected?.parcel_count} note="Parcelas del dataset en esta región" loading={loading} />
        <StatCard label="Riesgo productivo" value={null} note="Sin evaluación regional disponible" />
        <StatCard label="Producción potencial" value={null} note="Requiere un agregado de producción de la fuente" />
      </div>
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,1fr)]">
        <Panel className="min-w-0 p-5 sm:p-6">
          <p className="section-label">Comparación regional</p><h2 className="section-title mb-5 mt-2">Una lectura compartida del rendimiento</h2>
          <RegionComparison items={items} selected={selected} />
        </Panel>
        <Panel className="space-y-5 p-5 sm:p-6">
          <div><p className="section-label">Cómo interpretar</p><h2 className="section-title mt-2">La cobertura también cuenta.</h2></div>
          <p className="text-sm leading-relaxed text-text-mid">Una media puede corresponder solo a una parte de la región. Revisa siempre las parcelas con predicción y la versión del modelo antes de comparar.</p>
          <div className="space-y-3 border-t border-ink-700 pt-4 text-xs text-text-mid"><p><span className="text-moss-500">01</span> Misma unidad y versión para comparar.</p><p><span className="text-moss-500">02</span> Una región sin predicciones conserva su lugar.</p><p><span className="text-moss-500">03</span> El rendimiento medio no es producción total.</p></div>
          {selected?.model_version && <span className="status-chip">Modelo {selected.model_version}</span>}
          {isReal && definition && <div className="border-t border-ink-700 pt-4 text-xs leading-relaxed text-text-mid"><p>{definition.official_reference}</p><a className="mt-2 inline-block underline underline-offset-4" href={definition.region_source} target="_blank" rel="noreferrer">Consultar fuente estatal de la región</a><p className="mt-2">Agrupación adoptada por Cebada360 · {regionDefinitionVersion}. No es una regionalización definida por FIRA.</p></div>}
        </Panel>
      </div>
      <Panel className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-ink-700 p-5"><h2 className="section-title">Detalle por región</h2><span className="status-chip">{data ? `${items.length} resúmenes disponibles` : 'Consulta en curso'}</span></div>
        {items.length > 0 ? <div className="overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Cobertura y rendimiento medio por región, sin ponderar por superficie</caption><thead className="bg-ink-800/40 text-xs text-text-mid"><tr><th className="px-5 py-3">Región</th><th className="px-5 py-3">Cobertura</th><th className="px-5 py-3">Rendimiento medio</th><th className="px-5 py-3">Modelo</th></tr></thead><tbody>{items.map((item) => <tr key={item.region} className={`border-t border-ink-700 ${item.region === key ? 'bg-moss-900/15' : ''}`}><th scope="row" className="px-5 py-4 font-medium">{regionLabel(item.region)}</th><td className="px-5 py-4 tabular-nums">{item.predicted_count} / {item.parcel_count}</td><td className="px-5 py-4 tabular-nums">{item.predicted_count > 0 ? `${fmtNum(item.mean_prediction, 4)} ${item.unit}` : 'No disponible'}</td><td className="px-5 py-4 text-xs text-text-mid">{item.model_version ?? '—'}</td></tr>)}</tbody></table></div>
          : <div className="p-5"><PendingState title="Sin resúmenes regionales disponibles" description="La vista está preparada. Los indicadores se completarán cuando la fuente entregue resúmenes regionales." /></div>}
        {(unavailable.length > 0 || data?.unassigned_count > 0) && <details className="border-t border-ink-700 p-5 text-xs text-text-mid"><summary className="cursor-pointer">Disponibilidad de las regiones{unavailable.length > 0 ? ` · ${unavailable.length} pendientes` : ''}</summary><ul className="mt-3 space-y-2">{unavailable.map((item) => <li key={item.region}>{regionLabel(item.region)}: {item.message}</li>)}{data?.unassigned_count > 0 && <li>{data.unassigned_count} parcelas sin región asignada.</li>}</ul></details>}
      </Panel>
    </div>
  );
}
