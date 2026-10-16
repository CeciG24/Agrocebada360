import { useEffect, useState } from 'react';
import { Panel } from '../components/common/Panel';
import { DisclaimerBanner } from '../components/common/DisclaimerBanner';
import { Skeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';
import { KpiRegional } from '../components/regional/KpiRegional';
import { DistribucionRiesgo } from '../components/regional/DistribucionRiesgo';
import { TablaMunicipios } from '../components/regional/TablaMunicipios';
import { FactoresLimitantes } from '../components/regional/FactoresLimitantes';
import { repo } from '../data';

export function RegionalPage() {
  const [municipios, setMunicipios] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    repo.getRegionResumen()
      .then((data) => { if (alive) setMunicipios(data); })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setCargando(false));
    return () => { alive = false; };
  }, []);

  // ---------- Loading ----------
  if (cargando) {
    return (
      <div className="px-4 sm:px-6 pb-10 space-y-6 animate-fade-in">
        <DisclaimerBanner />
        <Skeleton className="h-8 w-56" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  // ---------- Error ----------
  if (error) {
    return (
      <div className="px-4 sm:px-6 pb-10 space-y-5">
        <DisclaimerBanner />
        <Panel className="p-4 sm:p-6 text-rose-300 text-sm">
          No se pudo cargar la información regional: {error}
        </Panel>
      </div>
    );
  }

  // ---------- Vacío ----------
  if (municipios.length === 0) {
    return (
      <div className="px-4 sm:px-6 pb-10 space-y-5">
        <DisclaimerBanner />
        <Panel>
          <EmptyState
            titulo="Aún no hay datos regionales"
            detalle="La fuente no devolvió municipios. Si estás en modo real, revisa la conexión o activa el modo demo."
          />
        </Panel>
      </div>
    );
  }

  // ---------- Métricas agregadas ----------
  // Se agregan todas las regiones que entrega la fuente; no se descarta ninguna
  // en silencio. La media es por parcela (sin ponderar por superficie), como
  // define el contrato público; la cobertura se muestra de forma explícita.
  const totalParcelas = municipios.reduce((s, m) => s + m.n_parcelas, 0);
  const totalSuperficie = municipios.reduce((s, m) => s + m.superficie_total_ha, 0);
  const totalProduccion = municipios.reduce((s, m) => s + m.produccion_total_t, 0);
  const rendimientoPromedio =
    totalParcelas > 0
      ? municipios.reduce((s, m) => s + m.rendimiento_promedio_t_ha * m.n_parcelas, 0) / totalParcelas
      : null;
  const reducidas = municipios.filter((m) => m.n_parcelas < 5).length;

  return (
    <div className="px-4 sm:px-6 pb-12 space-y-6">
      <DisclaimerBanner />

      {/* Encabezado */}
      <div>
        <h1 className="text-3xl font-semibold text-text-hi tracking-tight">
          Inteligencia regional
        </h1>
        <p className="mt-1.5 text-sm text-text-mid">
          Vista agregada de la producción esperada en la región. Se incluyen todas
          las regiones disponibles; las de muestra reducida se señalan.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiRegional
          label="Parcelas analizadas"
          value={totalParcelas}
          hint={`${municipios.length} regiones${reducidas > 0 ? ` · ${reducidas} con menos de 5 parcelas` : ''}`}
        />
        <KpiRegional
          label="Superficie analizada"
          value={totalSuperficie.toFixed(1)}
          unit="ha"
          hint="Suma de superficies de las regiones incluidas"
        />
        <KpiRegional
          label="Producción potencial agregada"
          value={totalProduccion.toFixed(0)}
          unit="t"
          hint="Estimación a partir del rendimiento × superficie"
        />
        <KpiRegional
          label="Rendimiento promedio"
          value={rendimientoPromedio !== null ? rendimientoPromedio.toFixed(2) : '—'}
          unit={rendimientoPromedio !== null ? 't/ha' : ''}
          hint="Media por parcela (sin ponderar por superficie)"
        />
      </div>

      {/* Distribución de riesgo */}
      <Panel className="p-4 sm:p-6">
        <h2 className="text-lg font-semibold text-text-hi mb-5">
          Distribución de riesgo por municipio
        </h2>
        <DistribucionRiesgo municipios={municipios} />
      </Panel>

      {/* Tabla de municipios */}
      <Panel className="p-4 sm:p-6">
        <TablaMunicipios municipios={municipios} />
      </Panel>

      {/* Factores limitantes */}
      <Panel className="p-4 sm:p-6">
        <FactoresLimitantes municipios={municipios} />
      </Panel>

      {/* Nota metodológica */}
      <Panel className="p-5">
        <p className="text-sm leading-relaxed text-text-mid">
          <b className="text-text-hi">Nota metodológica:</b> Los indicadores
          regionales se calculan a partir de las predicciones por parcela. Los
          promedios de rendimiento son medias por parcela, sin ponderar por
          superficie. Las regiones con menos de 5 parcelas se incluyen, pero sus
          cifras tienen poca muestra y deben leerse con cautela.
        </p>
      </Panel>
    </div>
  );
}