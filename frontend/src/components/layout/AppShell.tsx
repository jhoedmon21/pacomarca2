/**
 * Estructura general: sidebar + header + contenido + footer.
 * El contenido se desplaza según el estado del sidebar (solo escritorio).
 */
import type { ReactNode } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { useI18n } from '../../i18n'
import { cn } from '../../lib/utils'
import { Footer } from './Footer'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function AppShell({ children }: { children: ReactNode }) {
  const sidebarAbierto = useAppStore((s) => s.sidebarAbierto)
  const { t } = useI18n()

  return (
    <div className="min-h-screen bg-bg text-fg">
      {/* Enlace para saltar al contenido (teclado / lectores de pantalla) */}
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-accent-fg"
      >
        {t('common.saltar')}
      </a>

      <Sidebar />

      <div className={cn('flex min-h-screen flex-col', sidebarAbierto ? 'lg:pl-64' : 'lg:pl-16')}>
        <Header />
        <main id="contenido" className="mx-auto w-full max-w-7xl 2xl:max-w-[1536px] flex-1 space-y-6 px-4 py-6 lg:px-8">
          {children}
        </main>
        <Footer />
      </div>
    </div>
  )
}
