/** Estadísticas resumen de la capa activa. */
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import type { LayerId } from '../types'

export function useStats(lat: number, lon: number, years: number, layer: LayerId) {
  return useQuery({
    queryKey: ['stats', lat.toFixed(3), lon.toFixed(3), years, layer],
    queryFn: () => api.stats(lat, lon, years, layer),
    staleTime: 10 * 60 * 1000,
    retry: 1,
  })
}
