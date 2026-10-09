/** Clima actual del punto de control (refresco cada 10 min). */
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

export function useWeather(lat: number, lon: number) {
  return useQuery({
    queryKey: ['clima', lat.toFixed(2), lon.toFixed(2)],
    queryFn: () => api.clima(lat, lon),
    staleTime: 10 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
    retry: 1,
  })
}
