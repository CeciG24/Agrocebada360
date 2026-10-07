import { Component } from 'react';

export class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-2xl border border-rose-700/40 bg-rose-950/30 p-6 text-rose-200">
          <p className="font-semibold">Algo falló al mostrar esta parcela.</p>
          <p className="mt-1 text-sm text-rose-300/80">
            {this.state.error?.message ?? 'Error desconocido.'}
          </p>
          <button
            type="button"
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 rounded-lg border border-rose-700/50 px-3 py-1.5 text-sm hover:bg-rose-900/30 transition"
          >
            Reintentar
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}