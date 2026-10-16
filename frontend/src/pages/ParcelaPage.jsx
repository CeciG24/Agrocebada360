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
  const [estado, setEstado] = useState({ id: null });
  const [corte, setCorte] = useState('octubre');
  useEffect(() => {
    let alive = true;
    Promise.allSettled([
      repo.getParcelaById(id), repo.getVecinos(id, 3), repo.getContextoMunicipal(id),
      repo.getCortesTemporales(id), repo.getGeometrias(),
    ]).then(([p, v, c, co, g]) => {
      if (!alive) return;
      if (p.status === 'rejected' || !p.value) {
        setEstado({ id, error: p.reason?.message ?? 'No se encontró la parcela solicitada.' });
        return;
      }
      setEstado({ id, parcela: p.value,
        vecinos: v.status === 'fulfilled' && Array.isArray(v.value) ? v.value : [],
        contexto: c.status === 'fulfilled' ? c.value : null,
        cortes: co.status === 'fulfilled' && Array.isArray(co.value) ? co.value : [],
        geometrias: g.status === 'fulfilled' ? g.value : null,
        avisos: [c.status === 'rejected' ? `Resumen regional: ${c.reason.message}` : null,
          g.status === 'rejected' ? 'Geometrías no disponibles.' : null].filter(Boolean),
      });
    });
    return () => { alive = false; };
  }, [id]);

  if (estado.id !== id) return <Skeleton className="h-80 mx-6" />;
  if (estado.error) return (
    <div className="px-6 space-y-4"><BackButton label="Volver al dashboard" to="/" />
      <Panel><EmptyState titulo="No pudimos mostrar esta parcela" detalle={estado.error} /></Panel>
    </div>
  );
  const { parcela, vecinos, contexto, cortes, geometrias, avisos } = estado;
  const cierre = cortes.length === 0 || corte === 'octubre';
  const delCorte = cortes.find((c) => c?.corte === corte)?.rendimiento_t_ha;
  const rendimiento = esNum(delCorte) ? delCorte : cierre && esNum(parcela.rendimiento_t_ha) ? parcela.rendimiento_t_ha : null;
  const unit = parcela.meta ? parcela.prediction_unit : 't/ha';
  const superficie = esNum(parcela.superficie_ha) ? parcela.superficie_ha : null;
  const produccion = rendimiento !== null && superficie !== null && unit === 't/ha' ? rendimiento * superficie : null;

  return (
    <div className="px-4 sm:px-6 pb-12 space-y-6">
      <BackButton label="Volver al dashboard" to="/" />
      <DisclaimerBanner />
      <Panel className="p-4 sm:p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div><h1 className="text-3xl font-semibold">{parcela.id}</h1>
            <p className="text-text-mid">{parcela.meta ? `Región: ${parcela.region ?? 'no disponible'}` : parcela.municipio}</p>
          </div>
          <RiskBadge nivel={cierre ? parcela.riesgo : null} />
          {cortes.length > 0 && <SelectorCorte valor={corte} onChange={setCorte} />}
        </div>
        {[...avisos, ...(parcela.avisos ?? [])].map((aviso) => <p key={aviso} role="status" className="text-sm text-amber-300">{aviso}</p>)}
        <div className="grid grid-cols-3 gap-3">
          <MiniKpi label="Rendimiento estimado" value={fmtNum(rendimiento, 4)} unit={rendimiento !== null ? unit : ''} />
          <MiniKpi label="Producción potencial" value={fmtNum(produccion, 1)} unit={produccion !== null ? 't' : ''} />
          <MiniKpi label="Superficie" value={fmtNum(superficie, 1)} unit={superficie !== null ? 'ha' : ''} />
        </div>
        <p className="text-sm text-text-lo">{parcela.meta
          ? `Ciclo ${parcela.meta.cycle} · límite de información ${parcela.meta.data_cutoff} · modelo ${parcela.model_version ?? 'no disponible'}`
          : `Demostración · datos hasta ${corte} de 2025`}</p>
        {!cierre && <p className="text-text-lo">Predicción temprana. Los complementos del cierre se muestran al seleccionar octubre.</p>}
      </Panel>
      <Panel className="p-4 sm:p-6 space-y-5">
        <h2 className="text-lg font-semibold">Riesgo e incertidumbre</h2>
        <RangoProbable estimado={rendimiento} rango={cierre ? parcela.rango_probable : null} unit={unit}
          level={parcela.interval_level} method={parcela.interval_method} />
        {cierre && parcela.riesgo_descripcion && <p>{parcela.riesgo_descripcion} · método {parcela.risk_method_version}</p>}
        {cierre && parcela.ood_flag && <p className="text-amber-300">Esta parcela se parece poco a las vistas durante entrenamiento.</p>}
        <ComparacionVecinos vecinos={vecinos} actualId={parcela.id} />
      </Panel>
      <Panel className="p-4 sm:p-6 space-y-5">
        <h2 className="text-lg font-semibold">Factores que influyen en el resultado</h2>
        <ShapBars items={cierre && Array.isArray(parcela.shap) ? parcela.shap : []} context={parcela.explanation} />
        <NarrativaParcela texto={parcela.narrativa} />
        {cortes.length > 0 && <CurvaCortes cortes={cortes} corteActual={corte} />}
      </Panel>
      <Panel className="p-4 sm:p-6 space-y-5">
        <h2 className="text-lg font-semibold">Contexto territorial</h2>
        <MiniMapaContexto parcela={parcela} vecinos={vecinos} geometrias={geometrias} />
        <ContextoMunicipal contexto={contexto} parcela={parcela} />
      </Panel>
    </div>
  );
}
