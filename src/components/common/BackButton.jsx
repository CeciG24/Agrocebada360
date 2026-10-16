import { useNavigate } from 'react-router-dom';

export function BackButton({ to = -1, label = 'Volver' }) {
  const navigate = useNavigate();
  return (
    <button
      type="button"
      onClick={() => navigate(to)}
      className="inline-flex min-h-[40px] items-center gap-2 text-sm text-text-mid hover:text-text-hi transition"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      {label}
    </button>
  );
}