import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Panel } from '../components/common/Panel';
import { RiskBadge } from '../components/common/RiskBadge';
import { MiniKpi } from '../components/common/MiniKpi';
import { BackButton } from '../components/common/BackButton';
import { DisclaimerBanner } from '../components/common/DisclaimerBanner';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { Skeleton } from '../components/common/Skeleton';

import { RangoProbable } from '../components/parcela/RangoProbable';
import { ShapBars } from '../components/parcela/ShapBars';
import { NarrativaParcela } from '../components/parcela/NarrativaParcela';
import { SelectorCorte } from '../components/parcela/SelectorCorte';
import { ComparacionVecinos } from '../components/parcela/ComparacionVecinos';
import { MiniMapaContexto } from '../components/parcela/MiniMapaContexto';
import { CurvaCortes } from '../components/parcela/CurvaCortes';
import { ContextoMunicipal } from '../components/parcela/ContextoMunicipal';

import { repo } from '../data';

export function ParcelaPage() {
  const { id } = useParams();

  const [parcela, setParcela] = useState(null);
  const [vecinos, setVecinos] = useState([]);
  const [contexto, setContexto] = useState(null);
  const [cortes, setCortes] = useState([]);
  const [corte, setCorte] = useState('octubre');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    setCargando(true);
    setError(null);
    setParcela(null);
    setVecinos([]);
    setContexto(null);
    setCortes([]);

    Promise.all([
      repo.getParcelaById(id),
      repo.getVecinos(id, 3),
      repo.getContextoMunicipal(id),
      repo.getCortesTemporales(id),
    ])
      .then(([p, v, c, co]) => {
        if (!alive) return;
        setParcela(p);
        setVecinos(v);
        setContexto(c);
        setCortes(co);
      })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setCargando(false));

    return () => { alive = false; };
  }, [id]);

  // ---------- Estado: cargando ----------
  if (cargando) {
    return (
      <div className="px-6 pb-12 space-y-6 animate-fade-in">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-14 w-full" />

        <Panel className="p-6 space-y-5">
          <div className="flex justify-between items-start gap-4">
            <div className="space-y-2">
              <Skeleton className="h-9 w-48" />
              <Skeleton className="h-4 w-72" />
            </div>
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-64" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
          <Skeleton className="h-4 w-64" />
        </Panel>

        <Panel className="p-6 space-y-5">
          <Skeleton className="h-6 w-56" />
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-4 w-48" />
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </Panel>

        <Panel className="p-6 space-y-5">
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

        <Panel className="p-6 space-y-5">
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
      <div className="px-6 pb-10 space-y-4">
        <BackButton label="Volver al dashboard" to="/" />
        <Panel className="p-6 text-rose-300 text-sm">
          No se pudo cargar la parcela: {error ?? 'no encontrada'}
        </Panel>
      </div>
    );
  }

  // ---------- Estado: content ----------
  const corteInfo = cortes.find((c) => c.corte === corte);
  const rendimientoMostrado = corteInfo?.rendimiento_t_ha ?? parcela.rendimiento_t_ha;

  return (
    <div className="px-6 pb-12 space-y-6">
      {/* Volver */}
      <BackButton label="Volver al dashboard" to="/" />

      {/* Banner superior */}
      <DisclaimerBanner />

      {/* Cabecera + Módulo 1 */}
      <Panel className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-text-hi tracking-tight">
              {parcela.id}
            </h1>
            <p className="mt-1.5 text-sm text-text-lo">
              {parcela.municipio} · {parcela.superficie_ha.toFixed(1)} ha · confianza{' '}
              {parcela.confianza_pct}%
            </p>
          </div>
          <div className="flex items-center gap-3">
            <RiskBadge nivel={parcela.riesgo} />
            <SelectorCorte valor={corte} onChange={setCorte} />
          </div>
        </div>

        <div className="mt-6 grid grid-cols-3 gap-3">
          <MiniKpi
            label="Rendimiento estimado"
            value={rendimientoMostrado.toFixed(2)}
            unit="t/ha"
          />
          <MiniKpi
            label="Producción potencial"
            value={(rendimientoMostrado * parcela.superficie_ha).toFixed(1)}
            unit="t"
          />
          <MiniKpi
            label="Superficie"
            value={parcela.superficie_ha.toFixed(1)}
            unit="ha"
          />
        </div>

        <p className="mt-3 text-xs text-text-lo">
          Datos usados hasta <b className="text-text-mid capitalize">{corte}</b> de 2025.
          {corte !== 'octubre' &&
            ' Predicción temprana: el modelo aún no ve el ciclo completo.'}
        </p>
      </Panel>

      {/* Módulo 2 — Riesgo e incertidumbre */}
      <Panel className="p-6 space-y-6">
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
      <Panel className="p-6 space-y-6">
        <h2 className="text-lg font-semibold text-text-hi">
          ¿Por qué el modelo piensa eso?
        </h2>

        <ShapBars items={parcela.shap} />

        <NarrativaParcela texto={parcela.narrativa} />

        <CurvaCortes cortes={cortes} corteActual={corte} />
      </Panel>

      {/* Módulo 4 — Contexto territorial */}
      <Panel className="p-6 space-y-6">
        <h2 className="text-lg font-semibold text-text-hi">Contexto territorial</h2>

        <MiniMapaContexto parcela={parcela} vecinos={vecinos} />

        <ContextoMunicipal contexto={contexto} parcela={parcela} />
      </Panel>

      {/* Banner inferior */}
      <DisclaimerBanner />
    </div>
  );
}