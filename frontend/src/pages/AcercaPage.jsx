import { Link } from 'react-router-dom';
import { Panel } from '../components/common/Panel';
import { WorkspaceHeader } from '../components/common/WorkspaceHeader';
import { DisclaimerBanner } from '../components/common/DisclaimerBanner';

const MODULES = [
  { number: '01', title: 'Rendimiento', question: '¿Qué se espera de esta parcela?', text: 'Estimación puntual con su unidad, ciclo y versión de modelo. Lo que falta se indica como pendiente.', tag: 'Estimar', to: '/' },
  { number: '02', title: 'Incertidumbre y riesgo', question: '¿Con qué contexto debe leerse?', text: 'Intervalos y riesgo productivo cuando estén disponibles. La ausencia de riesgo no significa riesgo bajo.', tag: 'Contextualizar', to: '/' },
  { number: '03', title: 'Explicabilidad', question: '¿Qué influye en la estimación?', text: 'Factores que contribuyen al resultado de cada parcela. Una explicación describe al modelo, no establece causas.', tag: 'Comprender', to: '/' },
  { number: '04', title: 'Perspectiva territorial', question: '¿Cómo se compara con su región?', text: 'Medias por parcela y cobertura de predicciones, conservando unidad y versión para comparar.', tag: 'Comparar', to: '/regional' },
];

export function AcercaPage() {
  return (
    <div className="workspace">
      <WorkspaceHeader eyebrow="Cebada360 · Reto AgroCebada 2026" title="De una estimación a una lectura útil."
        description="Un espacio para explorar parcelas de cebada, consultar resultados y comprender la evidencia que los acompaña.">
        <Link to="/" className="status-chip hover:border-moss-700 hover:text-text-hi">Explorar parcelas <span aria-hidden="true">↗</span></Link>
      </WorkspaceHeader>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Los cuatro módulos de Cebada360">
        {MODULES.map((item) => <Panel key={item.number} className="flex flex-col p-5 sm:p-6"><div className="flex items-center justify-between"><span className="text-2xl font-light tabular-nums text-moss-500/80">{item.number}</span><span className="status-chip">{item.tag}</span></div><h2 className="mt-6 text-lg font-semibold">{item.title}</h2><p className="mt-2 text-sm text-text-hi">{item.question}</p><p className="mt-3 flex-1 text-sm leading-relaxed text-text-mid">{item.text}</p><Link to={item.to} className="mt-5 inline-flex min-h-10 items-center gap-2 text-xs font-semibold text-moss-500 hover:text-text-hi">Explorar módulo <span aria-hidden="true">↗</span></Link></Panel>)}
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="p-5 sm:p-6"><p className="section-label">Alcance y limitaciones</p><h2 className="section-title mt-2">Conocer los límites es parte de la lectura.</h2><ul className="mt-5 space-y-4 text-sm leading-relaxed text-text-mid">
          <li><b className="font-medium text-text-hi">Un ciclo específico.</b> El ciclo objetivo es abril–octubre de 2025. La transferencia a otros ciclos requiere validación.</li>
          <li><b className="font-medium text-text-hi">Explicación sin causalidad.</b> Una contribución indica cómo responde el modelo; no prueba el efecto de una práctica agrícola.</li>
          <li><b className="font-medium text-text-hi">Incertidumbre condicionada.</b> Los intervalos, si existen, necesitan método y cobertura documentados; no son garantías por parcela.</li>
          <li><b className="font-medium text-text-hi">Cobertura visible.</b> Algunos módulos o regiones pueden estar pendientes. No se completan con resultados de otra fuente.</li>
        </ul></Panel>
        <Panel className="p-5 sm:p-6"><p className="section-label">Uso responsable</p><h2 className="section-title mt-2">Evidencia para acompañar decisiones.</h2><p className="mt-5 text-sm leading-relaxed text-text-mid">Las estimaciones son insumos productivos complementarios. No sustituyen la observación en campo, el criterio agronómico ni la validación del contexto de cada parcela.</p><div className="mt-5 space-y-3 border-t border-ink-700 pt-5"><p className="text-sm text-text-mid"><span className="font-medium text-text-hi">Demo y mock identificados.</span> Los resultados de ejemplo no representan rendimientos reales.</p><p className="text-sm text-text-mid"><span className="font-medium text-text-hi">Sin decisiones crediticias.</span> No se aprueban créditos, se asignan montos ni se califica a productores.</p><p className="text-sm text-text-mid"><span className="font-medium text-text-hi">Versiones coherentes.</span> Predicción y explicación deben corresponder al mismo modelo.</p></div></Panel>
      </div>
      <DisclaimerBanner />
      <footer className="flex flex-wrap justify-between gap-2 border-t border-ink-700 pt-4 text-xs text-text-mid"><span>Cebada360 · Exploración, predicción e interpretación</span><span>Datos · Modelado · Validación · API · Experiencia de usuario</span></footer>
    </div>
  );
}
