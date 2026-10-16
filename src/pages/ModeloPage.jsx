import { useEffect, useState } from 'react';
import { Panel } from '../components/common/Panel';
import { Skeleton } from '../components/common/Skeleton';
import { MetricaCard } from '../components/modelo/MetricaCard';
import { ComparacionCV } from '../components/modelo/ComparacionCV';
import { CurvaCortesModelo } from '../components/modelo/CurvaCortesModelo';
import { TablaAblacion } from '../components/modelo/TablaAblacion';
import { CardReproducibilidad } from '../components/modelo/CardReproducibilidad';
import { repo } from '../data';

export function ModeloPage() {
  const [metricas, setMetricas] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    repo.getMetricasModelo()
      .then((data) => { if (alive) setMetricas(data); })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setCargando(false));
    return () => { alive = false; };
  }, []);

  // ---------- Loading ----------
  if (cargando) {
    return (
      <div className="px-4 sm:px-6 pb-10 space-y-6 animate-fade-in">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-96" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-72 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  // ---------- Error ----------
  if (error || !metricas) {
    return (
      <div className="px-4 sm:px-6 pb-10">
        <Panel className="p-4 sm:p-6 text-rose-300 text-sm">
          No se pudieron cargar las métricas del modelo: {error ?? 'sin datos'}
        </Panel>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 pb-12 space-y-6">
      {/* Encabezado */}
      <div>
        <h1 className="text-3xl font-semibold text-text-hi tracking-tight">
          Métricas del modelo
        </h1>
        <p className="mt-1.5 text-sm text-text-mid max-w-3xl">
          Resultados del modelo oficial y su desempeño fuera de muestra. Se reporta
          tanto la validación aleatoria como la espacial, además de la curva de
          predicción por corte temporal y el aporte de cada familia de features.
        </p>
      </div>

      {/* Bloque 1 — Métricas principales del modelo oficial */}
      <div>
        <div className="text-base text-text-mid mb-3">
          Modelo oficial — {metricas.modelo_oficial}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <MetricaCard
            label="RMSE"
            value={metricas.rmse.toFixed(2)}
            unit="t/ha"
            hint="Error cuadrático medio — mismo horizonte"
            variant="highlight"
          />
          <MetricaCard
            label="MAE"
            value={metricas.mae.toFixed(2)}
            unit="t/ha"
            hint="Error absoluto medio — más interpretable"
          />
          <MetricaCard
            label="R²"
            value={metricas.r2.toFixed(2)}
            hint="Varianza explicada por el modelo"
          />
        </div>
      </div>

      {/* Bloque 2 — CV aleatoria vs espacial */}
      <Panel className="p-4 sm:p-6">
        <ComparacionCV
          cvAleatoria={metricas.cv_aleatoria}
          cvEspacial={metricas.cv_espacial}
        />
      </Panel>

      {/* Bloque 3 — Cortes temporales */}
      <Panel className="p-4 sm:p-6">
        <CurvaCortesModelo cortes={metricas.cortes_temporales} />
      </Panel>

      {/* Bloque 4 — Ablación */}
      <Panel className="p-4 sm:p-6">
        <TablaAblacion ablacion={metricas.ablacion} />
      </Panel>

      {/* Bloque 5 — Reproducibilidad */}
      <CardReproducibilidad />

      {/* Bloque 6 — Nota final de rigor */}
      <Panel className="p-5">
        <p className="text-sm leading-relaxed text-text-mid">
          <b className="text-text-hi">Nota de rigor:</b> las métricas provienen de
          validación cruzada fuera de muestra. Los hiperparámetros se ajustaron
          dentro de cada fold, nunca antes. La partición de 59 parcelas de
          evaluación no se usó para tuning. Todos los números mostrados son
          reproducibles desde el repositorio.
        </p>
      </Panel>
    </div>
  );
}