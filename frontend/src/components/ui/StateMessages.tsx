/**
 * Estados amigables: error (con reintento), vacío y chip de carga.
 * Nunca se muestra una "pantalla rota" al usuario.
 */
import { Inbox, RefreshCw, TriangleAlert } from 'lucide-react'
import { useI18n } from '../../i18n'
import { Button } from './Button'

export function ErrorState({
  titulo,
  mensaje,
  onReintentar,
}: {
  titulo?: string
  mensaje?: string
  onReintentar?: () => void
}) {
  const { t } = useI18n()
  return (
    <div role="alert" className="flex flex-col items-center gap-3 p-8 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-danger/10 text-danger">
        <TriangleAlert aria-hidden="true" className="h-6 w-6" />
      </span>
      <div>
        <p className="font-bold">{titulo ?? t('common.error')}</p>
        <p className="mt-1 max-w-sm text-sm text-muted">{mensaje ?? t('common.errorMensaje')}</p>
      </div>
      {onReintentar && (
        <Button variant="outline" size="sm" onClick={onReintentar}>
          <RefreshCw aria-hidden="true" className="h-4 w-4" />
          {t('common.reintentar')}
        </Button>
      )}
    </div>
  )
}

export function EmptyState({ titulo, mensaje }: { titulo?: string; mensaje?: string }) {
  const { t } = useI18n()
  return (
    <div role="status" className="flex flex-col items-center gap-3 p-8 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-2 text-muted">
        <Inbox aria-hidden="true" className="h-6 w-6" />
      </span>
      <div>
        <p className="font-bold">{titulo ?? t('common.vacio')}</p>
        <p className="mt-1 max-w-sm text-sm text-muted">{mensaje ?? t('common.vacioMensaje')}</p>
      </div>
    </div>
  )
}
