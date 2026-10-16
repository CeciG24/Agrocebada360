import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GridParcelas } from '../components/mapa/GridParcelas';
import { MapaParcelas } from '../components/mapa/MapaParcelas';
import { ParcelaDetalle } from '../components/parcela/ParcelaDetalle';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { Panel } from '../components/common/Panel';
import { Skeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';
import { WorkspaceHeader } from '../components/common/WorkspaceHeader';
import { StatCard } from '../components/common/StatCard';
import { repo } from '../data';
import { useDemoStore } from '../store/demoStore';

export function DashboardPage() {
  const navigate = useNavigate();
  const modoDemo = useDemoStore((s) => s.modoDemo);
  const [resumen, setResumen] = useState([]);
  const [geometrias, setGeometrias] = useState(null);
  const [parcela, setParcela] = useState(null);
  const [seleccionada, setSeleccionada] = useState(null);
  const [cargandoLista, setCargandoLista] = useState(true);
  const [error, setError] = useState(null);
  const [detalleError, setDetalleError] = useState(null);

  useEffect(() => {
    let alive = true;
    Promise.all([repo.getAllParcelas(), repo.getGeometrias().catch(() => null)])
      .then(([data, geo]) => {
        if (!alive) return;
        setResumen(data); setGeometrias(geo);
        if (data.length > 0) setSeleccionada(data[0].id);
      }).catch((e) => alive && setError(e.message)).finally(() => alive && setCargandoLista(false));
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!seleccionada) return;
    let alive = true;
    repo.getParcelaById(seleccionada)
      .then((p) => alive && setParcela(p))
      .catch((e) => alive && setDetalleError({ id: seleccionada, message: e.message }));
    return () => { alive = false; };
  }, [seleccionada]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key !== 'Enter' || parcela?.id !== seleccionada || !parcela || e.defaultPrevented) return;
      if (e.target.closest?.('a, button, input, select, textarea, summary')) return;
      navigate(`/parcela/${encodeURIComponent(parcela.id)}`);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [parcela, seleccionada, navigate]);

  const parcelasMostradas = resumen.map((p) => p.id === parcela?.id ? { ...p, ...parcela } : p);
  const ids = new Set(resumen.map((p) => p.id));
  const geometriasDisponibles = geometrias ? new Set(geometrias.features.filter((f) => f.geometry && ids.has(f.properties?.id ?? f.id)).map((f) => f.properties?.id ?? f.id)).size : null;
  const regiones = new Set(resumen.map((p) => p.region ?? (modoDemo ? p.municipio : null)).filter((v) => v !== null)).size;
  const cicloFuente = resumen[0]?.meta?.cycle;
  const ciclo = cicloFuente === '2025-04/2025-10' ? 'Abr–oct 2025' : cicloFuente ?? (modoDemo ? 'Abr–oct 2025' : null);
  const cargandoDetalle = seleccionada && parcela?.id !== seleccionada;

  return (
    <div className="workspace">
      <WorkspaceHeader eyebrow="Exploración productiva" title="Cada parcela, una historia en datos."
        description="Explora el territorio, consulta el rendimiento esperado y conoce los factores que acompañan cada estimación.">
        <span className="status-chip">{modoDemo ? 'Demostración local' : 'Consulta por API'}</span>
        <a href="#lectura-parcela" className="status-chip hover:border-moss-700 hover:text-text-hi">Leer parcela seleccionada <span aria-hidden="true">↗</span></a>
      </WorkspaceHeader>
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4" aria-label="Indicadores del catálogo">
        <StatCard label="Parcelas en catálogo" value={error ? null : resumen.length} loading={cargandoLista} note="Universo cargado de la fuente actual" accent />
        <StatCard label="Con geometría" value={error ? null : geometriasDisponibles} loading={cargandoLista} note="Parcelas con un contorno disponible" />
        <StatCard label="Regiones del catálogo" value={error ? null : regiones} loading={cargandoLista} note={modoDemo ? 'Agrupaciones de demostración' : 'Claves regionales entregadas por la API'} />
        <StatCard label="Ciclo analizado" value={ciclo} loading={cargandoLista} note="La disponibilidad de datos se indica por módulo" />
      </div>
      <div className="grid items-stretch gap-5 xl:grid-cols-[minmax(0,1.3fr)_minmax(360px,1fr)]">
        {cargandoLista ? <Panel className="min-h-[440px] p-6"><Skeleton className="h-9 w-48" /><Skeleton className="mt-5 h-80" /></Panel>
          : error ? <Panel className="p-6"><p role="alert">No se pudo cargar el listado: {error}</p></Panel>
            : resumen.length === 0 ? <Panel><EmptyState titulo="No hay parcelas para mostrar" detalle="La fuente consultada todavía no entrega parcelas." /></Panel>
              : geometrias?.features?.length > 0
                ? <MapaParcelas parcelas={parcelasMostradas} geometrias={geometrias} seleccionadaId={seleccionada} onSelect={setSeleccionada} onAbrir={() => seleccionada && navigate(`/parcela/${encodeURIComponent(seleccionada)}`)} />
                : <GridParcelas parcelas={parcelasMostradas} seleccionadaId={seleccionada} onSelect={setSeleccionada} />}
        <section id="lectura-parcela" className="min-w-0 scroll-mt-32" aria-label="Lectura de la parcela seleccionada">
          <ErrorBoundary>
            {detalleError?.id === seleccionada ? <Panel className="p-6"><p role="alert">{detalleError.message}</p></Panel>
              : cargandoDetalle ? <Panel className="space-y-5 p-6"><Skeleton className="h-10 w-40" /><Skeleton className="h-32" /><Skeleton className="h-48" /></Panel>
                : <ParcelaDetalle parcela={parcela?.id === seleccionada ? parcela : null} onVerDetalle={() => parcela && navigate(`/parcela/${encodeURIComponent(parcela.id)}`)} />}
          </ErrorBoundary>
        </section>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-700 pt-4 text-xs text-text-mid">
        <p>La predicción y sus complementos se consultan por parcela; el catálogo no implica cobertura predictiva completa.</p>
        <span>Explorar → estimar → comprender</span>
      </div>
    </div>
  );
}
