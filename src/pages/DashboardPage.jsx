import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GridParcelas } from '../components/mapa/GridParcelas';
import { MapaParcelas } from '../components/mapa/MapaParcelas';
import { ParcelaDetalle } from '../components/parcela/ParcelaDetalle';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { Panel } from '../components/common/Panel';
import { Skeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';
import { repo } from '../data';

export function DashboardPage() {
  const navigate = useNavigate();

  const [resumen, setResumen] = useState([]);
  const [geometrias, setGeometrias] = useState(null);
  const [parcela, setParcela] = useState(null);
  const [seleccionada, setSeleccionada] = useState(null);
  const [cargandoLista, setCargandoLista] = useState(true);
  const [error, setError] = useState(null);

  // El detalle está cargando mientras la parcela seleccionada aún no coincide
  // con la que se pidió (se deriva, no se guarda en estado).
  const cargandoDetalle = Boolean(seleccionada) && parcela?.id !== seleccionada && !error;

  // Cargar listado de parcelas
  useEffect(() => {
    let alive = true;

    // Las geometrías son opcionales: si fallan o no existen, se usa la cuadrícula.
    Promise.all([repo.getAllParcelas(), repo.getGeometrias().catch(() => null)])
      .then(([data, geo]) => {
        if (!alive) return;
        setResumen(data);
        setGeometrias(geo);
        if (data.length > 0) setSeleccionada(data[0].id);
      })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setCargandoLista(false));

    return () => { alive = false; };
  }, []);

  // Cargar detalle de la parcela seleccionada
  useEffect(() => {
    if (!seleccionada) return;
    let alive = true;

    repo.getParcelaById(seleccionada)
      .then((p) => { if (alive) setParcela(p); })
      .catch((e) => alive && setError(e.message));

    return () => { alive = false; };
  }, [seleccionada]);

  // Atajo: Enter navega al detalle de la parcela seleccionada
  useEffect(() => {
    const onKey = (e) => {
      if (e.key !== 'Enter' || !parcela || e.defaultPrevented) return;
      // Si el foco está en un enlace/botón/campo, Enter ya tiene su propio significado
      // (antes, Enter sobre "Regional" también abría la ficha de la parcela).
      if (e.target.closest?.('a, button, input, select, textarea, summary')) return;
      navigate(`/parcela/${parcela.id}`);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [parcela, navigate]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 px-4 sm:px-6 pb-10">
      {/* ---------- Columna izquierda: grid de parcelas ---------- */}
      {cargandoLista ? (
        <Panel className="p-5 space-y-4 animate-fade-in">
          <Skeleton className="h-5 w-56" />
          <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[4/3] w-full" />
            ))}
          </div>
          <div className="pt-4 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-48" />
          </div>
        </Panel>
      ) : error ? (
        <Panel className="p-4 sm:p-6 text-rose-300 text-sm">
          No se pudo cargar el listado: {error}
        </Panel>
      ) : resumen.length === 0 ? (
        <Panel>
          <EmptyState
            titulo="No hay parcelas para mostrar"
            detalle="El servicio respondió sin parcelas. Si estás en modo real, revisa la conexión o activa el modo demo."
          />
        </Panel>
      ) : geometrias?.features?.length > 0 ? (
        <MapaParcelas
          parcelas={resumen}
          geometrias={geometrias}
          seleccionadaId={seleccionada}
          onSelect={setSeleccionada}
          onAbrir={() => seleccionada && navigate(`/parcela/${seleccionada}`)}
        />
      ) : (
        <GridParcelas
          parcelas={resumen}
          seleccionadaId={seleccionada}
          onSelect={setSeleccionada}
        />
      )}

      {/* ---------- Columna derecha: preview de parcela ---------- */}
      <ErrorBoundary>
        {cargandoDetalle && !parcela ? (
          <Panel className="p-4 sm:p-6 space-y-6 animate-fade-in">
            {/* Cabecera */}
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2">
                <Skeleton className="h-7 w-32" />
                <Skeleton className="h-4 w-56" />
              </div>
              <Skeleton className="h-10 w-24" />
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-3 gap-3">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>

            {/* Rango probable */}
            <div className="space-y-3">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-6 w-full" />
              <Skeleton className="h-4 w-48" />
            </div>

            {/* SHAP */}
            <div className="space-y-3">
              <Skeleton className="h-5 w-52" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-11/12" />
              <Skeleton className="h-4 w-10/12" />
            </div>

            {/* Narrativa */}
            <Skeleton className="h-16 w-full" />

            {/* Botón */}
            <Skeleton className="h-12 w-full" />
          </Panel>
        ) : (
          <ParcelaDetalle
            parcela={parcela}
            onVerDetalle={() => parcela && navigate(`/parcela/${parcela.id}`)}
          />
        )}
      </ErrorBoundary>
    </div>
  );
}