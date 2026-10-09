/** Serie temporal del índice activo (mantiene datos previos al refrescar). */
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import type { IndexId } from '../types'

export function useTimeseries(lat: number, lon: number, years: number, index: IndexId) {
  return useQuery({
    queryKey: ['serie', lat.toFixed(3), lon.toFixed(3), years, index],
    queryFn: () => api.serie(lat, lon, years, index),
    staleTime: 10 * 60 * 1000,
    retry: 1,
    placeholderData: (previa) => previa,
  })
}
