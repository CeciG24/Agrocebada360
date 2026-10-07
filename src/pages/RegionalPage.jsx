import { useEffect, useState } from 'react';
import { Panel } from '../components/common/Panel';
import { DisclaimerBanner } from '../components/common/DisclaimerBanner';
import { Skeleton } from '../components/common/Skeleton';
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
      <div className="px-6 pb-10 space-y-6 animate-fade-in">
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
      <div className="px-6 pb-10 space-y-5">
        <DisclaimerBanner />
        <Panel className="p-6 text-rose-300 text-sm">
          No se pudo cargar la información regional: {error}
        </Panel>
      </div>
    );
  }

  // ---------- Métricas agregadas ----------
  // Solo cuenta municipios con muestra suficiente para el resumen
  const conMuestra = municipios.filter((m) => m.n_parcelas >= 5);

  const totalParcelas = conMuestra.reduce((s, m) => s + m.n_parcelas, 0);
  const totalSuperficie = conMuestra.reduce((s, m) => s + m.superficie_total_ha, 0);
  const totalProduccion = conMuestra.reduce((s, m) => s + m.produccion_total_t, 0);
  const rendimientoPromedioPonderado =
    totalSuperficie > 0
      ? conMuestra.reduce(
          (s, m) => s + m.rendimiento_promedio_t_ha * m.superficie_total_ha,
          0,
        ) / totalSuperficie
      : 0;

  return (
    <div className="px-6 pb-12 space-y-6">
      <DisclaimerBanner />

      {/* Encabezado */}
      <div>
        <h1 className="text-3xl font-semibold text-text-hi tracking-tight">
          Inteligencia regional
        </h1>
        <p className="mt-1.5 text-sm text-text-mid">
          Vista agregada de la producción esperada en la región. Solo se incluyen
          municipios con muestra suficiente para un análisis representativo.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiRegional
          label="Parcelas analizadas"
          value={totalParcelas}
          hint={`${conMuestra.length} municipios con muestra suficiente`}
        />
        <KpiRegional
          label="Superficie analizada"
          value={totalSuperficie.toFixed(1)}
          unit="ha"
          hint="Suma de superficies con muestra ≥ 5"
        />
        <KpiRegional
          label="Producción potencial agregada"
          value={totalProduccion.toFixed(0)}
          unit="t"
          hint="Estimación a partir del rendimiento × superficie"
        />
        <KpiRegional
          label="Rendimiento promedio"
          value={rendimientoPromedioPonderado.toFixed(2)}
          unit="t/ha"
          hint="Ponderado por superficie"
        />
      </div>

      {/* Distribución de riesgo */}
      <Panel className="p-6">
        <h2 className="text-lg font-semibold text-text-hi mb-5">
          Distribución de riesgo por municipio
        </h2>
        <DistribucionRiesgo municipios={conMuestra} />
      </Panel>

      {/* Tabla de municipios */}
      <Panel className="p-6">
        <TablaMunicipios municipios={municipios} />
      </Panel>

      {/* Factores limitantes */}
      <Panel className="p-6">
        <FactoresLimitantes municipios={conMuestra} />
      </Panel>

      {/* Nota metodológica */}
      <Panel className="p-5">
        <p className="text-sm leading-relaxed text-text-mid">
          <b className="text-text-hi">Nota metodológica:</b> Los indicadores
          regionales se calculan a partir de las predicciones por parcela. Se
          excluyen municipios con menos de 5 parcelas para evitar conclusiones
          sobre muestras no representativas. Los promedios de rendimiento están
          ponderados por superficie.
        </p>
      </Panel>
    </div>
  );
}