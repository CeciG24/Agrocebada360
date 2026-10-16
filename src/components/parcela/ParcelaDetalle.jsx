import { Panel } from '../common/Panel';
import { RiskBadge } from '../common/RiskBadge';
import { MiniKpi } from '../common/MiniKpi';
import { RangoProbable } from './RangoProbable';
import { ShapBars } from './ShapBars';
import { NarrativaParcela } from './NarrativaParcela';
import { EmptyState } from '../common/EmptyState';

export function ParcelaDetalle({ parcela, onVerDetalle }) {
  if (!parcela) {
    return (
      <Panel>
        <EmptyState
          titulo="Selecciona una parcela"
          detalle="Toca una parcela del mapa para ver su rendimiento esperado, su riesgo y por qué el modelo llegó a esa cifra."
        />
      </Panel>
    );
  }

  // Si un campo no llega, se muestra como no disponible: nunca se rellena con
  // un valor que parezca un resultado real.
  const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
  const rendimiento = num(parcela.rendimiento_t_ha);
  const produccion  = num(parcela.produccion_potencial_t);
  const superficie  = num(parcela.superficie_ha);
  const rango       = Array.isArray(parcela.rango_probable)
                      && parcela.rango_probable.length === 2
                      && parcela.rango_probable.every((v) => num(v) !== null)
                        ? parcela.rango_probable
                        : null;
  const shap        = Array.isArray(parcela.shap) ? parcela.shap : [];
  const riesgo      = parcela.riesgo ?? null;
  const confianzaPct = num(parcela.confianza_pct);
  const corte       = parcela.corte_temporal ?? '—';
  const narrativa   = parcela.narrativa || 'Sin narrativa disponible para esta parcela.';

  return (
    <Panel className="p-4 sm:p-6 space-y-6 animate-fade-up">
      {/* Cabecera */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-text-hi tracking-tight">
            {parcela.id}
          </h2>
          <p className="mt-1 text-sm text-text-lo">
            Datos hasta {corte}
            {confianzaPct !== null && ` · confianza ${confianzaPct}%`}
          </p>
        </div>
        <RiskBadge nivel={riesgo} />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-3">
        <MiniKpi label="Rendimiento" value={rendimiento !== null ? rendimiento.toFixed(2) : '—'} unit={rendimiento !== null ? 't/ha' : ''} />
        <MiniKpi label="Producción"  value={produccion !== null ? produccion.toFixed(1) : '—'}  unit={produccion !== null ? 't' : ''} />
        <MiniKpi label="Superficie"  value={superficie !== null ? superficie.toFixed(1) : '—'}  unit={superficie !== null ? 'ha' : ''} />
      </div>

      {rendimiento !== null && rango ? (
        <RangoProbable estimado={rendimiento} rango={rango} />
      ) : (
        <p className="text-sm text-text-lo">Rango probable no disponible para esta parcela.</p>
      )}

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