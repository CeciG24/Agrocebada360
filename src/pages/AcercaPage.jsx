import { Panel } from '../components/common/Panel';
import { DisclaimerBanner } from '../components/common/DisclaimerBanner';

// ---------- Secciones de texto ----------
const MODULOS = [
  {
    num: '01',
    titulo: 'Rendimiento',
    pregunta: '¿Cuánto se espera producir?',
    detalle:
      'Estimación puntual en toneladas por hectárea por parcela y producción potencial agregada (t/ha × superficie).',
  },
  {
    num: '02',
    titulo: 'Riesgo e incertidumbre',
    pregunta: '¿Qué tan confiable es y qué puede salir mal?',
    detalle:
      'Rango probable, semáforo de riesgo bajo/medio/alto y alerta si la parcela se parece poco a lo visto en entrenamiento.',
  },
  {
    num: '03',
    titulo: 'Explicabilidad',
    pregunta: '¿Por qué el modelo piensa eso?',
    detalle:
      'Contribuciones de cada familia de variables —vigor, humedad, estrés, clima, topografía— traducidas a lenguaje claro.',
  },
  {
    num: '04',
    titulo: 'Inteligencia territorial',
    pregunta: '¿Cómo se convierte en información útil?',
    detalle:
      'Vista agregada por municipio, superficie total, producción potencial y factores limitantes predominantes.',
  },
];

const LIMITACIONES = [
  {
    titulo: 'Muestra pequeña',
    detalle:
      '138 parcelas etiquetadas es un conjunto reducido. Aunque la validación es rigurosa, la estimación tiene un techo estadístico inherente.',
  },
  {
    titulo: 'Detección OOD frágil',
    detalle:
      'La alerta de "parcela fuera de distribución" es cualitativa. Con pocas muestras de referencia, no debe interpretarse como un score probabilístico.',
  },
  {
    titulo: 'Explicabilidad no causal',
    detalle:
      'Las contribuciones SHAP indican qué empujó la predicción, no qué causó el rendimiento. Agruparlas por familia mitiga la inestabilidad entre variables correlacionadas.',
  },
  {
    titulo: 'Corte temporal condicionado',
    detalle:
      'Las predicciones tempranas funcionan porque el modelo ve parte del ciclo. Un corte demasiado anticipado (por ejemplo, febrero) no tiene señal vegetativa suficiente.',
  },
  {
    titulo: 'Sin validación externa',
    detalle:
      'El modelo se entrena y evalúa sobre las mismas 197 parcelas. No se ha probado en municipios fuera de la región de entrenamiento.',
  },
  {
    titulo: 'Ciclo único evaluado',
    detalle:
      'El horizonte oficial es abril–octubre 2025. La transferibilidad a otros ciclos está fuera del alcance del reto.',
  },
];

const FUENTES = [
  { nombre: 'Rendimiento + área', detalle: '138 train / 59 predicción · objetivo oficial' },
  { nombre: 'BÁSICO',             detalle: 'Sentinel y Landsat · 2022–2025 · índices y nubosidad' },
  { nombre: 'PRO',                detalle: 'Planet · 2025 · NDVI, EVI, LAI, MSAVI' },
  { nombre: 'Clima',              detalle: 'CHIRPS precipitación + temperatura · 2022–2025' },
  { nombre: 'Topografía',         detalle: 'INEGI CEM · elevación y pendiente' },
  { nombre: 'Parcelas',           detalle: '197 polígonos con geometría real' },
];

export function AcercaPage() {
  return (
    <div className="px-6 pb-12 space-y-6 max-w-4xl mx-auto">
      {/* Encabezado */}
      <div className="animate-fade-up">
        <h1 className="text-3xl font-semibold text-text-hi tracking-tight">
          Acerca de Cebada360
        </h1>
        <p className="mt-1.5 text-sm text-text-mid">
          Metodología, limitaciones y uso responsable del producto.
        </p>
      </div>

      {/* Qué es */}
      <Panel className="p-6 animate-fade-up">
        <h2 className="text-lg font-semibold text-text-hi mb-3">
          Qué es Cebada360
        </h2>
        <p className="text-sm leading-relaxed text-text-mid">
          Cebada360 es una capa de inteligencia alrededor de un modelo predictivo
          de rendimiento de cebada de temporal. No entrega solo toneladas por
          hectárea: convierte la predicción en una lectura de confiabilidad, la
          explica, la sitúa en un contexto territorial y la traduce a indicadores
          productivos útiles como evidencia complementaria para el análisis de FIRA.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-text-mid">
          El alcance del reto es el ciclo <b className="text-text-hi">abril–octubre 2025</b>{' '}
          sobre <b className="text-text-hi">197 parcelas</b> de cebada de temporal,
          de las cuales 138 tienen rendimiento observado y 59 son las que se
          predicen.
        </p>
      </Panel>

      {/* Los 4 módulos */}
      <Panel className="p-6 animate-fade-up">
        <h2 className="text-lg font-semibold text-text-hi mb-5">
          Los cuatro módulos
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {MODULOS.map((m, idx) => (
            <div
              key={m.num}
              className="rounded-xl border border-ink-700/60 bg-ink-800/40 p-4
                         transition-all duration-200
                         hover:border-moss-700/40 hover:bg-ink-800/60
                         animate-fade-up"
              style={{ animationDelay: `${idx * 60}ms` }}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs font-mono text-moss-500 tracking-wider">
                  {m.num}
                </span>
                <span className="text-sm font-semibold text-text-hi">
                  {m.titulo}
                </span>
              </div>
              <div className="text-xs text-moss-500 italic mb-2">
                {m.pregunta}
              </div>
              <p className="text-sm leading-relaxed text-text-mid">
                {m.detalle}
              </p>
            </div>
          ))}
        </div>
      </Panel>

      {/* Fuentes de datos */}
      <Panel className="p-6 animate-fade-up">
        <h2 className="text-lg font-semibold text-text-hi mb-5">
          Fuentes de datos
        </h2>
        <div className="space-y-2">
          {FUENTES.map((f, idx) => (
            <div
              key={f.nombre}
              className="grid grid-cols-[160px_1fr] items-start gap-4
                         rounded-lg border border-ink-700/40 bg-ink-800/30
                         px-4 py-3 animate-fade-up"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <span className="text-sm font-medium text-text-hi">{f.nombre}</span>
              <span className="text-sm text-text-mid">{f.detalle}</span>
            </div>
          ))}
        </div>
      </Panel>

      {/* Metodología */}
      <Panel className="p-6 animate-fade-up">
        <h2 className="text-lg font-semibold text-text-hi mb-4">
          Decisiones metodológicas clave
        </h2>
        <ul className="space-y-3 text-sm leading-relaxed text-text-mid">
          <li className="flex gap-3">
            <span className="text-moss-500 mt-1 shrink-0">●</span>
            <span>
              <b className="text-text-hi">Los sensores no se mezclan.</b> Sentinel,
              Landsat y Planet se procesan por separado y se combinan como features
              al final, conservando trazabilidad de origen. Mezclar sus observaciones
              como equivalentes introduciría errores por diferencias de resolución,
              frecuencia y respuesta espectral.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-moss-500 mt-1 shrink-0">●</span>
            <span>
              <b className="text-text-hi">Sin información posterior al horizonte.</b>{' '}
              El modelo oficial no usa datos después de octubre de 2025. Los cortes
              tempranos (junio, julio-agosto, septiembre) miden qué tan pronto se
              puede anticipar el resultado final con información disponible hasta
              esa fecha.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-moss-500 mt-1 shrink-0">●</span>
            <span>
              <b className="text-text-hi">Doble validación: aleatoria y espacial.</b>{' '}
              La validación aleatoria compara modelos. La validación espacial mide
              generalización a zonas no vistas durante entrenamiento. La diferencia
              entre ambas es la prueba de rigor del modelo.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-moss-500 mt-1 shrink-0">●</span>
            <span>
              <b className="text-text-hi">Ajuste dentro del fold.</b> Imputadores,
              escaladores y selección de features se ajustan dentro de cada fold del
              cross-validation, nunca antes. La partición de 59 parcelas de evaluación
              no se usa para tuning.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-moss-500 mt-1 shrink-0">●</span>
            <span>
              <b className="text-text-hi">Incertidumbre calibrada.</b> Los intervalos
              se construyen con métodos como conformal prediction o regresión
              cuantílica, y se reporta su cobertura empírica. El rango probable
              acompaña siempre a la predicción puntual.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-moss-500 mt-1 shrink-0">●</span>
            <span>
              <b className="text-text-hi">Reproducibilidad total.</b> El CSV oficial
              de predicciones se genera desde el mismo pipeline del modelo ganador.
              La app, el reporte y el archivo enviado a FIRA no pueden tener
              resultados distintos.
            </span>
          </li>
        </ul>
      </Panel>

      {/* Limitaciones */}
      <Panel className="p-6 animate-fade-up">
        <h2 className="text-lg font-semibold text-text-hi mb-2">
          Limitaciones que declaramos
        </h2>
        <p className="text-sm text-text-mid mb-5">
          Un producto serio reconoce lo que no puede hacer. Estas son las
          limitaciones que el equipo identifica explícitamente.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {LIMITACIONES.map((l, idx) => (
            <div
              key={l.titulo}
              className="rounded-xl border border-amber-700/25 bg-amber-950/15 p-4
                         animate-fade-up"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                <span className="text-sm font-semibold text-amber-300">
                  {l.titulo}
                </span>
              </div>
              <p className="text-sm leading-relaxed text-text-mid">
                {l.detalle}
              </p>
            </div>
          ))}
        </div>
      </Panel>

      {/* Uso responsable — destacado */}
      <Panel className="p-6 border-amber-700/40 bg-amber-950/20 animate-fade-up">
        <div className="flex items-start gap-4">
          <div className="shrink-0 grid h-10 w-10 place-items-center rounded-xl
                          bg-amber-950/60 border border-amber-700/40">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-amber-400">
              <path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"
                    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-amber-200 mb-2">
              Uso responsable
            </h2>
            <p className="text-sm leading-relaxed text-amber-100/85">
              Cebada360 entrega <b>evidencia productiva complementaria</b> para el
              análisis de FIRA. <b>No aprueba ni rechaza créditos, no propone montos,
              no sustituye un análisis crediticio, no califica a un productor y no
              constituye una recomendación financiera.</b> Las predicciones, rangos,
              semáforos de riesgo y explicaciones son insumos técnicos que pueden
              complementar un proceso de análisis, nunca reemplazarlo.
            </p>
          </div>
        </div>
      </Panel>

      {/* Equipo y créditos */}
      <Panel className="p-6 animate-fade-up">
        <h2 className="text-lg font-semibold text-text-hi mb-5">
          Equipo
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { rol: 'Data / ETL + Geoespacial',    tarea: 'Pipeline de datos y features' },
            { rol: 'Machine Learning + Validación', tarea: 'Modelos, CV y selección' },
            { rol: 'ML avanzado + Riesgo',        tarea: 'Incertidumbre, OOD, SHAP' },
            { rol: 'Backend / MLOps',             tarea: 'API, versionado, CSV oficial' },
            { rol: 'Frontend / UX + Storytelling', tarea: 'App, demo y narrativa' },
          ].map((m, idx) => (
            <div
              key={m.rol}
              className="rounded-xl border border-ink-700/60 bg-ink-800/40 px-4 py-3
                         animate-fade-up"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <div className="text-sm font-medium text-text-hi">{m.rol}</div>
              <div className="text-xs text-text-lo mt-0.5">{m.tarea}</div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-6 border-t border-ink-700/60 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-text-lo text-xs uppercase tracking-wide mb-1">
              Contacto
            </div>
            <div className="text-text-mid">
              innovacion@fira.gob.mx
            </div>
          </div>
          <div>
            <div className="text-text-lo text-xs uppercase tracking-wide mb-1">
              Versión
            </div>
            <div className="text-text-mid">
              Cebada360 v0.1 · Reto AgroCebada FIRA 2026
            </div>
          </div>
        </div>
      </Panel>

      {/* Banner uso responsable al pie (por consistencia con otras páginas) */}
      <DisclaimerBanner />

      {/* Pie */}
      <div className="text-center text-xs text-text-lo py-6">
        Propuesta técnica de trabajo · Versión actualizada con dataset y precisiones del Comité
      </div>
    </div>
  );
}