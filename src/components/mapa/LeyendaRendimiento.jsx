export function LeyendaRendimiento() {
  const stops = ['#0f2a1a', '#14532d', '#166534', '#15803d', '#16a34a'];
  const clip = 'polygon(8% 12%, 94% 4%, 96% 92%, 4% 96%)';

  return (
    <div className="flex items-center gap-3 text-sm text-text-mid">
      <span>Menor</span>
      <div className="flex gap-1">
        {stops.map((c) => (
          <span
            key={c}
            className="h-3.5 w-6"
            style={{ backgroundColor: c, clipPath: clip }}
          />
        ))}
      </div>
      <span>Mayor</span>
    </div>
  );
}