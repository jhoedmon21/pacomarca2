/** Clasificación de hábitats del área de análisis. */
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

export function useClassification(lat: number, lon: number) {
  return useQuery({
    queryKey: ['clasificacion', lat.toFixed(2), lon.toFixed(2)],
    queryFn: () => api.clasificacion(lat, lon),
    staleTime: 60 * 60 * 1000, // la cobertura cambia poco: 1 h de frescura
    retry: 1,
  })
}
