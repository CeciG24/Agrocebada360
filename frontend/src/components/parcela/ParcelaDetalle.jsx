import { Panel } from '../common/Panel';
import { RiskBadge } from '../common/RiskBadge';
import { PendingState } from '../common/PendingState';
import { RangoProbable } from './RangoProbable';
import { FeatureHighlights } from './FeatureHighlights';
import { EmptyState } from '../common/EmptyState';
import { esNum, fmtNum } from '../../lib/format';

export function ParcelaDetalle({ parcela, onVerDetalle }) {
  if (!parcela) return <Panel><EmptyState titulo="Selecciona una parcela" detalle="Su rendimiento, incertidumbre y principales factores aparecerán aquí." /></Panel>;
  const rendimiento = esNum(parcela.rendimiento_t_ha) ? parcela.rendimiento_t_ha : null;
  const unit = parcela.meta ? parcela.prediction_unit : 't/ha';
  const rango = Array.isArray(parcela.rango_probable) && parcela.rango_probable.length === 2 && parcela.rango_probable.every(esNum)
    && rendimiento !== null && parcela.rango_probable[0] <= rendimiento && rendimiento <= parcela.rango_probable[1] ? parcela.rango_probable : null;
  const factors = Array.isArray(parcela.shap) ? parcela.shap : [];
  return (
    <Panel className="overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-ink-700 px-5 py-4">
        <div className="min-w-0"><p className="section-label">Parcela seleccionada</p><h2 className="mt-1 break-all text-xl font-semibold">{parcela.id}</h2></div>
        <span className="status-chip">{parcela.meta ? `Región ${parcela.region ?? 'pendiente'}` : parcela.municipio ?? 'Ubicación pendiente'}</span>
      </div>
      <div className="space-y-5 p-5">
        <section className="rounded-xl border border-moss-700/30 bg-moss-900/20 p-4" aria-label="Rendimiento de la parcela">
          <div className="flex items-center justify-between gap-3"><h3 className="section-label">01 / Rendimiento estimado</h3><span className="h-1.5 w-1.5 rounded-full bg-moss-500" aria-hidden="true" /></div>
          <div className="mt-3 flex flex-wrap items-baseline gap-2"><p className="text-4xl font-semibold tracking-tight tabular-nums">{fmtNum(rendimiento, 4)}</p>{rendimiento !== null && <span className="text-sm text-text-mid">{unit}</span>}</div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-mid">
            <span>Superficie: {esNum(parcela.superficie_ha) ? `${fmtNum(parcela.superficie_ha, 1)} ha` : 'pendiente'}</span>
            <span>Producción: {esNum(parcela.produccion_potencial_t) ? `${fmtNum(parcela.produccion_potencial_t, 1)} t` : 'pendiente'}</span>
          </div>
          <p className="mt-3 border-t border-moss-700/20 pt-3 text-[11px] leading-relaxed text-text-mid">{parcela.meta ? `Ciclo ${parcela.meta.cycle} · límite ${parcela.meta.data_cutoff}` : 'Estimación sintética de demostración'}{parcela.model_version ? ` · ${parcela.model_version}` : ''}</p>
        </section>
        <section aria-label="Incertidumbre y riesgo" className="space-y-3">
          <h3 className="section-label">02 / Incertidumbre y riesgo</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {rango ? <div className="rounded-xl border border-ink-700 p-3"><RangoProbable estimado={rendimiento} rango={rango} unit={unit} level={parcela.interval_level} method={parcela.interval_method} /></div>
              : <PendingState compact title="Intervalo pendiente" description="La fuente aún no entrega un intervalo para esta estimación." />}
            {parcela.riesgo ? <div className="flex items-center justify-between gap-3 rounded-xl border border-ink-700 p-3"><div><p className="text-xs text-text-mid">Riesgo productivo</p><p className="mt-1 text-xs text-text-mid">Complemento de interpretación</p></div><RiskBadge nivel={parcela.riesgo} /></div>
              : <PendingState compact title="Riesgo pendiente" description="Sin clasificación disponible. No equivale a riesgo bajo." />}
          </div>
        </section>
        <section className="space-y-3 border-t border-ink-700 pt-5" aria-label="Tres factores principales">
          <div className="flex items-center justify-between gap-3"><h3 className="section-label">03 / Explicación</h3><span className="text-[10px] font-semibold uppercase tracking-wider text-moss-500">Top 3 factores</span></div>
          <FeatureHighlights items={factors} context={parcela.explanation} />
          {parcela.narrativa && <p className="border-l-2 border-moss-700 pl-3 text-xs leading-relaxed text-text-mid">{parcela.narrativa}</p>}
        </section>
        {parcela.avisos?.length > 0 && <details className="rounded-lg border border-ink-700 p-3 text-xs text-text-mid"><summary className="cursor-pointer">Disponibilidad de los módulos · {parcela.avisos.length} avisos</summary><ul className="mt-2 list-disc space-y-1 pl-4">{parcela.avisos.map((aviso) => <li key={aviso}>{aviso}</li>)}</ul></details>}
        {onVerDetalle && <button type="button" onClick={onVerDetalle} className="flex min-h-11 w-full items-center justify-between gap-3 rounded-xl border border-moss-700/50 bg-moss-900 px-4 py-3 text-sm font-semibold text-moss-500 transition-colors hover:bg-moss-700 hover:text-white">
          Ver detalle completo de {parcela.id}<span aria-hidden="true">↗</span>
        </button>}
      </div>
    </Panel>
  );
}
