/** Validación cruzada MODIS vs Sentinel-2 para el punto (frescura: 1 h). */
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

export function useCrosscheck(lat: number, lon: number) {
  return useQuery({
    queryKey: ['crosscheck', lat.toFixed(2), lon.toFixed(2)],
    queryFn: () => api.crosscheck(lat, lon),
    staleTime: 60 * 60 * 1000,
    retry: 1,
  })
}
