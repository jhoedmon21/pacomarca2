/**
 * Tema claro/oscuro/sistema con tokens CSS.
 * - 'system' sigue prefers-color-scheme y reacciona en vivo a sus cambios.
 * - La preferencia se persiste en localStorage.
 * - Se aplica la clase .dark (Tailwind) y data-theme (tokens) sobre <html>.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

export type Tema = 'light' | 'dark' | 'system'

interface TemaContexto {
  tema: Tema
  temaResuelto: 'light' | 'dark'
  setTema: (tema: Tema) => void
  alternarTema: () => void
}

const Contexto = createContext<TemaContexto | null>(null)

function resolverPreferencia(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [tema, setTemaState] = useState<Tema>(() => {
    const guardado = localStorage.getItem('pacomarca-theme')
    return guardado === 'light' || guardado === 'dark' || guardado === 'system'
      ? guardado
      : 'system'
  })
  const [temaResuelto, setTemaResuelto] = useState<'light' | 'dark'>(() =>
    tema === 'system' ? resolverPreferencia() : tema,
  )

  useEffect(() => {
    const aplicar = () => {
      const resuelto = tema === 'system' ? resolverPreferencia() : tema
      setTemaResuelto(resuelto)
      document.documentElement.classList.toggle('dark', resuelto === 'dark')
      document.documentElement.dataset.theme = resuelto
    }
    aplicar()
    localStorage.setItem('pacomarca-theme', tema)

    if (tema !== 'system') return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    media.addEventListener('change', aplicar)
    return () => media.removeEventListener('change', aplicar)
  }, [tema])

  const alternarTema = useCallback(() => {
    setTemaState((actual) =>
      actual === 'light' ? 'dark' : actual === 'dark' ? 'system' : 'light',
    )
  }, [])

  return (
    <Contexto.Provider value={{ tema, temaResuelto, setTema: setTemaState, alternarTema }}>
      {children}
    </Contexto.Provider>
  )
}

export function useTheme(): TemaContexto {
  const ctx = useContext(Contexto)
  if (!ctx) throw new Error('useTheme debe usarse dentro de ThemeProvider')
  return ctx
}
