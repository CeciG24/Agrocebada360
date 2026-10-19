import { useEffect, useState } from 'react';
import { Panel } from '../components/common/Panel';
import { WorkspaceHeader } from '../components/common/WorkspaceHeader';
import { StatCard } from '../components/common/StatCard';
import { PendingState } from '../components/common/PendingState';
import { ObservedPredicted } from '../components/modelo/ObservedPredicted';
import { repo } from '../data';
import { fmtNum, esNum } from '../lib/format';
import { useDemoStore } from '../store/demoStore';

export function ModeloPage() {
  const modoDemo = useDemoStore((s) => s.modoDemo);
  const [result, setResult] = useState({ mode: null, metricas: null, error: null });
  useEffect(() => {
    let alive = true;
    repo.getMetricasModelo().then((metricas) => alive && setResult({ mode: modoDemo, metricas, error: null }))
      .catch((e) => alive && setResult({ mode: modoDemo, metricas: null, error: e.message }));
    return () => { alive = false; };
  }, [modoDemo]);
  const loading = result.mode !== modoDemo;
  const metricas = loading ? null : result.metricas;
  const error = loading ? null : result.error;
  const features = metricas?.features ?? [];
  const peak = Math.max(...features.map((f) => f.mean_abs_shap), 0.001);
  return <div className="workspace">
    <WorkspaceHeader eyebrow="Transparencia del modelo" title="Entender también cómo se estima."
      description="Identidad, desempeño y evidencia de validación del predictor, con sus alcances y limitaciones.">
      <span className="status-chip">{modoDemo ? 'Métricas sintéticas · demo local' : 'Ficha versionada · validación interna'}</span>
    </WorkspaceHeader>
    {error && <p role="alert" className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-200">No se pudo verificar la ficha del modelo: {error}</p>}
    <Panel className="flex flex-col justify-between gap-5 p-5 sm:flex-row sm:items-center sm:p-6">
      <div className="min-w-0"><p className="section-label">Identidad del modelo</p><h2 className="mt-2 break-words text-xl font-semibold">{metricas?.modelo_oficial ?? (loading ? 'Verificando el modelo…' : 'Ficha del modelo no disponible')}</h2>
        <p className="mt-2 text-sm leading-relaxed text-text-mid">{modoDemo ? 'Nombre y resultados sintéticos de demostración.' : metricas ? 'Evidencia del desarrollo del modelo. No corresponde a la calificación del conjunto oculto de FIRA.' : 'Se necesita una API compatible con la ficha versionada del frontend.'}</p>
        {metricas?.n_features && <div className="mt-3 flex flex-wrap gap-2 text-xs text-text-mid"><span className="status-chip">{metricas.n_features} variables climáticas</span><span className="status-chip">{metricas.n_train} parcelas etiquetadas</span><span className="status-chip">{metricas.n_evaluation} parcelas de evaluación</span></div>}
      </div><div className="shrink-0 rounded-xl border border-ink-600 bg-ink-800/40 p-4"><p className="section-label">Versión</p><p className="mt-2 text-sm font-medium">{metricas?.model_version ?? 'No disponible'}</p></div>
    </Panel>
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Métricas de validación interna">
      <StatCard label="RMSE · CV aleatoria" value={esNum(metricas?.rmse) ? fmtNum(metricas.rmse, 4) : null} unit={metricas ? 't/ha' : null} note="Error cuadrático medio · menor es mejor" loading={loading} accent />
      <StatCard label="MAE · CV aleatoria" value={esNum(metricas?.mae) ? fmtNum(metricas.mae, 4) : null} unit={metricas ? 't/ha' : null} note="Error absoluto medio · menor es mejor" loading={loading} />
      <StatCard label="R² · CV aleatoria" value={esNum(metricas?.r2) ? fmtNum(metricas.r2, 4) : null} note="Coeficiente de determinación; no es porcentaje de acierto" loading={loading} />
      <StatCard label="RMSE · CV espacial" value={esNum(metricas?.cv_espacial?.rmse) ? fmtNum(metricas.cv_espacial.rmse, 4) : null} unit={metricas?.cv_espacial ? 't/ha' : null} note="Diagnóstico en grupos geográficos separados" loading={loading} />
    </div>
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,1fr)]">
      <Panel className="min-w-0 space-y-4 p-5 sm:p-6"><div><p className="section-label">Desempeño predictivo</p><h2 className="section-title mt-2">Observado vs. predicho</h2></div><ObservedPredicted oof={metricas?.oof} /></Panel>
      <Panel className="space-y-5 p-5 sm:p-6"><div><p className="section-label">Rigor de evaluación</p><h2 className="section-title mt-2">Método de validación</h2></div>
        {metricas?.cv_aleatoria || metricas?.cv_espacial ? <div className="space-y-3">{[['CV aleatoria', metricas.cv_aleatoria], ['CV espacial', metricas.cv_espacial]].map(([label, cv]) => <div key={label} className="rounded-xl border border-ink-700 bg-ink-800/30 p-4"><h3 className="text-sm font-medium">{label}</h3><p className="mt-2 text-sm tabular-nums">RMSE {fmtNum(cv?.rmse, 4)} {esNum(cv?.rmse) ? 't/ha' : ''} · R² {fmtNum(cv?.r2, 4)}</p><p className="mt-2 text-xs leading-relaxed text-text-mid">{cv?.method ?? 'Resultado sintético de demostración.'}</p>{cv?.seed !== undefined && <p className="mt-2 text-xs text-text-mid">Semilla {cv.seed}</p>}</div>)}<p className="text-xs leading-relaxed text-text-mid">Las validaciones responden a particiones diferentes y se presentan por separado. La selección del modelo utiliza esta evidencia; no es una evaluación externa independiente.</p></div>
          : <PendingState title="Validación no disponible" description="No hay resultados compatibles para esta vista." />}
      </Panel>
    </div>
    <div className="grid gap-5 lg:grid-cols-2">
      <Panel className="min-w-0 space-y-4 p-5 sm:p-6"><div><p className="section-label">Variables del modelo</p><h2 className="section-title mt-2">Features principales</h2></div>
        {features.length ? <><p className="text-xs leading-relaxed text-text-mid">Media del impacto absoluto SHAP en {metricas.shap_population} parcelas de evaluación, en t/ha. Es importancia predictiva, no un efecto causal.</p><ol className="space-y-4">{features.slice(0, 6).map((f) => <li key={f.feature}><div className="flex items-start justify-between gap-3 text-xs"><span className="min-w-0 break-words" title={f.feature}>{f.friendly_name}</span><span className="shrink-0 tabular-nums text-moss-500">{fmtNum(f.mean_abs_shap, 4)} t/ha</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-ink-800" aria-hidden="true"><div className="h-full rounded-full bg-moss-500" style={{ width: `${f.mean_abs_shap / peak * 100}%` }} /></div></li>)}</ol>
        <details className="rounded-lg border border-ink-700 p-3 text-xs"><summary className="cursor-pointer">Ver las {features.length} variables y sus unidades de entrada</summary><ul className="mt-3 space-y-4">{features.map((f) => <li key={f.feature} className="space-y-1"><p>{f.friendly_name} · {f.variable_unit}</p><code className="block break-all text-text-mid">{f.feature}</code><p className="leading-relaxed text-text-mid">{f.definition} {f.temporal_window}</p></li>)}</ul></details><p className="text-xs leading-relaxed text-text-mid">Las unidades de entrada (mm o °C) son distintas del impacto SHAP (t/ha). Variables correlacionadas, como precipitación total y media, pueden compartir importancia.</p></> : <PendingState title="Variables no disponibles" description="No hay un esquema compatible integrado a esta vista." />}
      </Panel>
      <Panel className="min-w-0 space-y-4 p-5 sm:p-6"><div><p className="section-label">Procedencia</p><h2 className="section-title mt-2">Fuentes de datos</h2></div>
        {metricas?.sources?.length ? <>{metricas.sources.map((source) => <div key={source.path} className="space-y-3 rounded-xl border border-ink-700 p-4"><h3 className="text-sm font-medium">{source.name}</h3><p className="text-sm text-moss-500">{source.window}</p><p className="text-xs leading-relaxed text-text-mid">{source.transformation}</p><p className="text-xs leading-relaxed text-text-mid">{source.note}</p><code className="block break-all text-xs text-text-mid">{source.path}</code></div>)}<p className="text-xs leading-relaxed text-text-mid">El predictor final utiliza clima. Las fuentes satelitales y la topografía se analizaron en experimentos, pero no se presentan como entradas de yield-v1.</p><p className="text-xs text-text-mid">Ciclo {metricas.meta.cycle} · corte técnico {metricas.meta.data_cutoff}</p></> : <PendingState title="Fuentes no disponibles" description="No hay procedencia compatible con el modelo consultado." />}
      </Panel>
    </div>
    {metricas?.limitations && <Panel className="space-y-4 p-5 sm:p-6"><h2 className="section-title">Limitaciones y lectura responsable</h2><ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-text-mid">{metricas.limitations.map((text) => <li key={text}>{text}</li>)}</ul><details className="rounded-lg border border-ink-700 p-3 text-xs text-text-mid"><summary className="cursor-pointer">Trazabilidad de la ficha de validación</summary><div className="mt-3 space-y-3 break-words"><p>Ficha incluida con el frontend y contrastada con una predicción de referencia de la API. Esa comprobación no certifica por sí sola el hash del artefacto servido.</p><p>Versión de datos: {metricas.data_version}</p><p className="break-all">SHA256 del modelo documentado: {metricas.model_sha256}</p>{Object.entries(metricas.provenance).map(([path, hash]) => <div key={path}><code className="block break-all">{path}</code><code className="block break-all text-text-lo">{hash}</code></div>)}</div></details></Panel>}
  </div>;
}
