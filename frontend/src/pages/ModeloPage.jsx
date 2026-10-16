import { useEffect, useState } from 'react';
import { Panel } from '../components/common/Panel';
import { WorkspaceHeader } from '../components/common/WorkspaceHeader';
import { StatCard } from '../components/common/StatCard';
import { PendingState } from '../components/common/PendingState';
import { ChartPlaceholder } from '../components/common/ChartPlaceholder';
import { repo } from '../data';
import { fmtNum, esNum } from '../lib/format';
import { useDemoStore } from '../store/demoStore';

export function ModeloPage() {
  const [metricas, setMetricas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const modoDemo = useDemoStore((s) => s.modoDemo);
  useEffect(() => {
    let alive = true;
    repo.getMetricasModelo().then((value) => alive && setMetricas(value)).catch((e) => alive && setError(e.message)).finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, []);
  return (
    <div className="workspace">
      <WorkspaceHeader eyebrow="Transparencia del modelo" title="Entender también cómo se estima."
        description="Identidad, desempeño y evidencia de validación en un mismo lugar. Los espacios pendientes se completan únicamente con información de la fuente.">
        <span className="status-chip">{modoDemo ? 'Métricas sintéticas · demo local' : 'Información de la fuente API'}</span>
      </WorkspaceHeader>
      {error && <p role="alert" className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-200">No se pudieron consultar las métricas: {error}</p>}
      <Panel className="flex flex-col justify-between gap-5 p-5 sm:flex-row sm:items-center sm:p-6">
        <div className="min-w-0"><p className="section-label">Identidad del modelo</p><h2 className="mt-2 break-words text-xl font-semibold">{metricas?.modelo_oficial ?? 'Identidad del modelo pendiente'}</h2><p className="mt-2 text-sm text-text-mid">{modoDemo ? 'Nombre y resultados de ejemplo; no describen el modelo final.' : 'Los detalles se mostrarán cuando estén disponibles en la fuente consultada.'}</p></div>
        <div className="shrink-0 rounded-xl border border-ink-600 bg-ink-800/40 p-4"><p className="section-label">Versión</p><p className="mt-2 text-sm font-medium">{metricas?.model_version ?? 'Pendiente de recibir'}</p></div>
      </Panel>
      <div className="grid gap-3 sm:grid-cols-3" aria-label="Métricas de evaluación">
        <StatCard label="RMSE" value={esNum(metricas?.rmse) ? fmtNum(metricas.rmse) : null} unit={metricas ? 't/ha' : null} note="Error cuadrático medio · menor es mejor" loading={loading} accent />
        <StatCard label="MAE" value={esNum(metricas?.mae) ? fmtNum(metricas.mae) : null} unit={metricas ? 't/ha' : null} note="Error absoluto medio · menor es mejor" loading={loading} />
        <StatCard label="R²" value={esNum(metricas?.r2) ? fmtNum(metricas.r2) : null} note="Coeficiente de determinación de la evaluación" loading={loading} />
      </div>
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,1fr)]">
        <Panel className="space-y-5 p-5 sm:p-6"><div><p className="section-label">Desempeño predictivo</p><h2 className="section-title mt-2">Observado vs. predicho</h2></div><ChartPlaceholder title="Comparación de predicciones" description="No hay pares de valores observados y predichos disponibles para esta gráfica." xLabel="Rendimiento observado" yLabel="Rendimiento predicho" /><p className="text-xs text-text-mid">La gráfica requiere predicciones de evaluación o fuera de muestra. No se reconstruye a partir de RMSE, MAE o R².</p></Panel>
        <Panel className="space-y-5 p-5 sm:p-6"><div><p className="section-label">Rigor de evaluación</p><h2 className="section-title mt-2">Método de validación</h2></div>
          {metricas?.cv_aleatoria || metricas?.cv_espacial ? <div className="space-y-3">{[['CV aleatoria', metricas.cv_aleatoria], ['CV espacial', metricas.cv_espacial]].map(([label, cv]) => <div key={label} className="rounded-xl border border-ink-700 bg-ink-800/30 p-4"><h3 className="text-sm font-medium">{label}</h3><p className="mt-2 text-xs text-text-mid">RMSE <span className="ml-2 font-semibold tabular-nums text-text-hi">{fmtNum(cv?.rmse)}{esNum(cv?.rmse) ? ' t/ha' : ''}</span></p></div>)}<p className="text-xs leading-relaxed text-text-mid">Los resultados de cada validación se muestran por separado. El detalle de particiones y parámetros sigue pendiente.</p></div>
            : <PendingState title="Validación pendiente" description="Sin protocolo ni resultados de validación integrados a esta vista." />}
        </Panel>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="space-y-4 p-5 sm:p-6"><div><p className="section-label">Variables del modelo</p><h2 className="section-title mt-2">Features principales</h2></div><PendingState title="Esquema de features pendiente" description="Los nombres y su importancia se mostrarán cuando exista información del modelo disponible en esta vista." /><p className="text-xs text-text-mid">La influencia en una parcela se consulta en su explicación; no se deduce de las métricas globales.</p></Panel>
        <Panel className="space-y-4 p-5 sm:p-6"><div><p className="section-label">Procedencia</p><h2 className="section-title mt-2">Fuentes de datos</h2></div><PendingState title="Fuentes del modelo pendientes" description="Se necesita la procedencia y la ventana temporal de las variables utilizadas por el modelo." /><p className="text-xs text-text-mid">La presencia de una fuente en el proyecto no implica que forme parte del modelo seleccionado.</p></Panel>
      </div>
      {!loading && !metricas && <p className="border-t border-ink-700 pt-4 text-xs text-text-mid">Métricas no disponibles. Los espacios visibles son estados pendientes, no resultados ni una simulación de desempeño.</p>}
    </div>
  );
}
