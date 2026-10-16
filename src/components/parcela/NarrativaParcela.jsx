export function NarrativaParcela({ texto }) {
  return (
    <p className="text-sm leading-relaxed text-text-mid">
      {texto || 'Sin narrativa disponible para esta parcela.'}
    </p>
  );
}