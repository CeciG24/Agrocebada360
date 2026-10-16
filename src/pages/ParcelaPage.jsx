import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Panel } from '../components/common/Panel';
import { RiskBadge } from '../components/common/RiskBadge';
import { MiniKpi } from '../components/common/MiniKpi';
import { BackButton } from '../components/common/BackButton';
import { DisclaimerBanner } from '../components/common/DisclaimerBanner';
import { Skeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';

import { RangoProbable } from '../components/parcela/RangoProbable';
import { ShapBars } from '../components/parcela/ShapBars';
import { NarrativaParcela } from '../components/parcela/NarrativaParcela';
import { SelectorCorte } from '../components/parcela/SelectorCorte';
import { ComparacionVecinos } from '../components/parcela/ComparacionVecinos';
import { MiniMapaContexto } from '../components/parcela/MiniMapaContexto';
import { CurvaCortes } from '../components/parcela/CurvaCortes';
import { ContextoMunicipal } from '../components/parcela/ContextoMunicipal';

import { repo } from '../data';
import { esNum, fmtNum } from '../lib/format';

export function ParcelaPage() {
  const { id } = useParams();

  // Un solo estado etiquetado con el id al que pertenece: mientras `estado.id`
  // no coincida con el id de la ruta, la página está cargando.
  const [estado, setEstado] = useState({
  id: null, parcela: null, vecinos: [], contexto: null, cortes: [], omitidos: [], geometrias: null, error: null,
});
  const [corte, setCorte] = useState('octubre');

  useEffect(() => {
  let alive = true;

  PPromise.allSettled([
  repo.getParcelaById(id),
  repo.getVecinos(id, 3),
  repo.getContextoMunicipal(id),
  repo.getCortesTemporales(id),
  repo.getGeometrias(),
]).then(([p, v, c, co, g]) => {
    if (!alive) return;
    if (p.status === 'rejected' || !p.value) {
      setEstado({
  id, parcela: null, vecinos: [], contexto: null, cortes: [], omitidos: [], geometrias: null,
  error: p.status === 'rejected' ? (p.reason?.message ?? 'error desconocido') : null,
});
      return;
    }
    const omitidos = [];
    if (v.status === 'rejected') omitidos.push('parcelas similares');
    if (c.status === 'rejected') omitidos.push('contexto municipal');
    if (co.status === 'rejected') omitidos.push('predicción por cortes');
    setEstado({
  id,
  parcela: p.value,
  vecinos: v.status === 'fulfilled' && Array.isArray(v.value) ? v.value : [],
  contexto: c.status === 'fulfilled' ? c.value : null,
  cortes: co.status === 'fulfilled' && Array.isArray(co.value) ? co.value : [],
  omitidos,
  // Sin geometrías el mini mapa usa su respaldo de cuadritos; no es un error.
  geometrias: g.status === 'fulfilled' ? g.value : null,
  error: null,
});
  });

  return () => { alive = false; };
}, [id]);

  const cargando = estado.id !== id;
  const { parcela, vecinos, contexto, cortes, omitidos, geometrias, error } = estado;

  // ---------- Estado: cargando ----------
  if (cargando) {
    return (
      <div className="px-4 sm:px-6 pb-12 space-y-6 animate-fade-in">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-14 w-full" />

        <Panel className="p-4 sm:p-6 space-y-5">
          <div className="flex justify-between items-start gap-4">
            <div className="space-y-2">
              <Skeleton className="h-9 w-48" />
              <Skeleton className="h-4 w-full max-w-[18rem]" />
            </div>
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-full max-w-[16rem]" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
          <Skeleton className="h-4 w-64" />
        </Panel>

        <Panel className="p-4 sm:p-6 space-y-5">
          <Skeleton className="h-6 w-56" />
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-4 w-48" />
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </Panel>

        <Panel className="p-4 sm:p-6 space-y-5">
          <Skeleton className="h-6 w-64" />
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-11/12" />
            <Skeleton className="h-4 w-10/12" />
            <Skeleton className="h-4 w-9/12" />
          </div>
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-32 w-full" />
        </Panel>

        <Panel className="p-4 sm:p-6 space-y-5">
          <Skeleton className="h-6 w-52" />
          <div className="grid grid-cols-4 gap-2">
            <Skeleton className="aspect-square w-full" />
            <Skeleton className="aspect-square w-full" />
            <Skeleton className="aspect-square w-full" />
            <Skeleton className="aspect-square w-full" />
          </div>
          <Skeleton className="h-4 w-72" />
          <Skeleton className="h-24 w-full" />
        </Panel>
      </div>
    );
  }

  // ---------- Estado: error o no encontrada ----------
  if (error || !parcela) {
    return (
      <div className="px-4 sm:px-6 pb-10 space-y-4">
        <BackButton label="Volver al dashboard" to="/" />
        <Panel>
          <EmptyState
            titulo="No pudimos mostrar esta parcela"
            detalle={error ?? 'No se encontró la parcela solicitada.'}
          />
        </Panel>
      </div>
    );
  }

  // Solo en 'octubre' se puede usar el valor final de la parcela; en un corte
// temprano sin dato se muestra '—', no el final.
const corteInfo = cortes.find((c) => c?.corte === corte);
const delCorte = esNum(corteInfo?.rendimiento_t_ha) ? corteInfo.rendimiento_t_ha : null;
const rendimientoMostrado =
  delCorte ?? (corte === 'octubre' && esNum(parcela.rendimiento_t_ha) ? parcela.rendimiento_t_ha : null);
const superficie = esNum(parcela.superficie_ha) ? parcela.superficie_ha : null;
const produccion =
  rendimientoMostrado !== null && superficie !== null ? rendimientoMostrado * superficie : null;

  return (
    <div className="px-4 sm:px-6 pb-12 space-y-6">
      {/* Volver */}
      <BackButton label="Volver al dashboard" to="/" />

      {/* Banner superior */}
      <DisclaimerBanner />

      {/* Cabecera + Módulo 1 */}
      <Panel className="p-4 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-text-hi tracking-tight">
              {parcela.id}
            </h1>
            <p className="mt-1.5 text-sm text-text-lo">
  {parcela.municipio ?? 'Municipio no disponible'} · {fmtNum(superficie, 1)} ha · confianza{' '}
  {esNum(parcela.confianza_pct) ? `${parcela.confianza_pct}%` : 'no disponible'}
</p>
{omitidos.length > 0 && (
  <p className="mt-1 text-xs text-amber-400/90" role="status">
    Sin datos de: {omitidos.join(', ')}.
  </p>
)}
          </div>
          <div className="flex w-full flex-wrap items-center gap-3 sm:w-auto">
            <RiskBadge nivel={parcela.riesgo} />
            <SelectorCorte valor={corte} onChange={setCorte} />
          </div>
        </div>

        <div className="mt-6 grid grid-cols-3 gap-3">
          <MiniKpi
  label="Rendimiento estimado"
  value={fmtNum(rendimientoMostrado, 2)}
  unit={rendimientoMostrado !== null ? 't/ha' : ''}
/>
<MiniKpi
  label="Producción potencial"
  value={fmtNum(produccion, 1)}
  unit={produccion !== null ? 't' : ''}
/>
<MiniKpi
  label="Superficie"
  value={fmtNum(superficie, 1)}
  unit={superficie !== null ? 'ha' : ''}
/>
        </div>

        <p className="mt-3 text-xs text-text-lo">
          Datos usados hasta <b className="text-text-mid capitalize">{corte}</b> de 2025.
          {corte !== 'octubre' &&
            ' Predicción temprana: el modelo aún no ve el ciclo completo.'}
        </p>
      </Panel>

      {/* Módulo 2 — Riesgo e incertidumbre */}
      <Panel className="p-4 sm:p-6 space-y-6">
        <h2 className="text-lg font-semibold text-text-hi">Riesgo e incertidumbre</h2>

        <RangoProbable
          estimado={rendimientoMostrado}
          rango={parcela.rango_probable}
        />

        {parcela.ood_flag && (
          <div className="rounded-lg border border-amber-700/40 bg-amber-950/30 px-4 py-3 text-sm text-amber-300">
            <b>Atención:</b> esta parcela se parece poco a las vistas durante
            entrenamiento. La predicción puede ser menos confiable de lo habitual.
          </div>
        )}

        <ComparacionVecinos vecinos={vecinos} actualId={parcela.id} />
      </Panel>

      {/* Módulo 3 — Explicabilidad */}
      <Panel className="p-4 sm:p-6 space-y-6">
        <h2 className="text-lg font-semibold text-text-hi">
          ¿Por qué el modelo piensa eso?
        </h2>

        <ShapBars items={Array.isArray(parcela.shap) ? parcela.shap : []} />

        <NarrativaParcela texto={parcela.narrativa} />

        <CurvaCortes cortes={cortes} corteActual={corte} />
      </Panel>

      {/* Módulo 4 — Contexto territorial */}
      <Panel className="p-4 sm:p-6 space-y-6">
        <h2 className="text-lg font-semibold text-text-hi">Contexto territorial</h2>

        <MiniMapaContexto parcela={parcela} vecinos={vecinos} geometrias={geometrias} />

        <ContextoMunicipal contexto={contexto} parcela={parcela} />
      </Panel>

      {/* Banner inferior */}
      <DisclaimerBanner />
    </div>
  );
}