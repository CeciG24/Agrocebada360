import { Panel } from '../common/Panel';
import { ParcelaTile } from './ParcelaTile';
import { LeyendaRendimiento } from './LeyendaRendimiento';

export function GridParcelas({ parcelas, seleccionadaId, onSelect }) {
  return (
    <Panel className="flex flex-col p-6 animate-fade-up">
      {/* Cabecera */}
      <div className="flex items-center gap-3 text-base text-text-mid">
        <span className="inline-block h-2 w-2 rounded-full bg-moss-500 animate-pulse" />
        <span>
          <b className="text-text-hi">{parcelas.length}</b> parcelas · rendimiento esperado
        </span>
      </div>

      {/* Grid con padding extra para absorber rotaciones y offsets */}
      <div className="mt-4 grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5
                      gap-x-3 gap-y-5
                      px-2 py-4">
        {parcelas.map((p) => (
          <ParcelaTile
            key={p.id}
            parcela={p}
            seleccionada={p.id === seleccionadaId}
            onClick={() => onSelect(p.id)}
          />
        ))}
      </div>

      {/* Leyenda al pie */}
      <div className="mt-auto pt-6 space-y-2">
        <LeyendaRendimiento />
        <p className="text-sm text-text-lo">Toca una parcela para abrir su ficha.</p>
      </div>
    </Panel>
  );
}