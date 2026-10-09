/**
 * Punto de entrada: providers de tema, i18n y consultas, y límite de error
 * global (si algo explota, pantalla amigable en lugar de blanco).
 */
import { Component, StrictMode, type ErrorInfo, type ReactNode } from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './theme/ThemeProvider'
import { I18nProvider } from './i18n'
import App from './App'
import './index.css'
import './pwa'

/** Límite de error global: última barrera contra pantallas en blanco. */
class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Error no capturado:', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
          <h1 className="text-xl font-extrabold">Ups, algo salió mal</h1>
          <p className="max-w-md text-sm text-muted">
            Ocurrió un error inesperado en la interfaz. Recarga la página; si persiste, avisa al
            equipo.
          </p>
          <button
            type="button"
            onClick={() => location.reload()}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-fg"
          >
            Recargar
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <I18nProvider>
          <QueryClientProvider client={queryClient}>
            <App />
          </QueryClientProvider>
        </I18nProvider>
      </ThemeProvider>
    </ErrorBoundary>
  </StrictMode>,
)
