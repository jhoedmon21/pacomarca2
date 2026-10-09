/**
 * Lee los tokens CSS del :root como colores reales, reactivo al tema.
 * Necesario para SVG/Recharts: var() en atributos de presentación
 * (stroke/fill) no tiene soporte garantizado en todos los navegadores,
 * así que se resuelven a "rgb(r g b)" desde JavaScript.
 */
import { useMemo } from 'react'
import { useTheme } from '../theme/ThemeProvider'

export function useThemeColors() {
  const { temaResuelto } = useTheme()
  return useMemo(() => {
    const estilos = getComputedStyle(document.documentElement)
    const leer = (token: string, respaldo: string) => {
      const canales = estilos.getPropertyValue(token).trim()
      return canales ? `rgb(${canales})` : respaldo
    }
    return {
      accent: leer('--accent', '#b1451c'),
      border: leer('--border', '#e3d9c8'),
      textSecondary: leer('--text-secondary', '#6d5f4b'),
    }
    // `temaResuelto` como dependencia: al cambiar el tema, se releen los tokens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [temaResuelto])
}
