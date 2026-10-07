import { Panel } from '../common/Panel';
import { RiskBadge } from '../common/RiskBadge';
import { MiniKpi } from '../common/MiniKpi';
import { RangoProbable } from './RangoProbable';
import { ShapBars } from './ShapBars';
import { NarrativaParcela } from './NarrativaParcela';

export function ParcelaDetalle({ parcela, onVerDetalle }) {
  if (!parcela) {
    return (
      <Panel className="p-6 text-text-lo text-sm">
        Selecciona una parcela para ver su ficha.
      </Panel>
    );
  }

  const rendimiento = parcela.rendimiento_t_ha ?? 0;
  const produccion  = parcela.produccion_potencial_t ?? 0;
  const superficie  = parcela.superficie_ha ?? 0;
  const rango       = parcela.rango_probable ?? [rendimiento - 0.3, rendimiento + 0.3];
  const shap        = Array.isArray(parcela.shap) ? parcela.shap : [];
  const riesgo      = parcela.riesgo ?? 'medio';
  const confianzaPct = parcela.confianza_pct ?? 0;
  const corte       = parcela.corte_temporal ?? '—';
  const narrativa   = parcela.narrativa || 'Sin narrativa disponible para esta parcela.';

  return (
    <Panel className="p-6 space-y-6 animate-fade-up">
      {/* Cabecera */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-text-hi tracking-tight">
            {parcela.id}
          </h2>
          <p className="mt-1 text-sm text-text-lo">
            Datos hasta {corte} · confianza {confianzaPct}%
          </p>
        </div>
        <RiskBadge nivel={riesgo} />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-3">
        <MiniKpi label="Rendimiento" value={rendimiento.toFixed(2)} unit="t/ha" />
        <MiniKpi label="Producción"  value={produccion.toFixed(1)}  unit="t" />
        <MiniKpi label="Superficie"  value={superficie.toFixed(1)}  unit="ha" />
      </div>

      <RangoProbable estimado={rendimiento} rango={rango} />

      {shap.length > 0 && <ShapBars items={shap} />}

      <NarrativaParcela texto={narrativa} />

      {/* Botón Ver detalle */}
      {onVerDetalle && (
        <div className="pt-2 border-t border-ink-700/60">
          <button
            type="button"
            onClick={onVerDetalle}
            className="group w-full inline-flex items-center justify-center gap-2 rounded-xl
                       bg-moss-900 border border-moss-700/50 px-4 py-3
                       text-sm font-semibold text-moss-500
                       transition-all duration-200
                       hover:bg-moss-700 hover:text-white hover:border-moss-600
                       active:scale-[0.98]"
          >
            Ver detalle completo de {parcela.id}
            <svg
              width="16" height="16" viewBox="0 0 24 24" fill="none"
              className="transition-transform duration-200 group-hover:translate-x-1"
            >
              <path
                d="M5 12h14M13 6l6 6-6 6"
                stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      )}
    </Panel>
  );
}