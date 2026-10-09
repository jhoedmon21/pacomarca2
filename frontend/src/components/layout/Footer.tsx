/**
 * Pie de página: firma y fuentes de datos.
 */
import { useI18n } from '../../i18n'

export function Footer() {
  const { t } = useI18n()
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto flex max-w-7xl 2xl:max-w-[1536px] flex-col items-center gap-1 px-4 py-6 text-center text-xs text-muted lg:px-8">
        <p className="font-semibold">{t('footer.firma')}</p>
        <p>{t('footer.fuentes')}</p>
        <p>© {new Date().getFullYear()} Pacomarca Scientific Suite</p>
      </div>
    </footer>
  )
}
