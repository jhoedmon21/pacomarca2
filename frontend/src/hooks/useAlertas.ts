/** Historial de alertas persistidas por el job diario (base de datos). */
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

export function useAlertas(limite = 50, puntoId?: number) {
  return useQuery({
    queryKey: ['alertas', limite, puntoId ?? 'todos'],
    queryFn: () => api.alertas.listar(limite, puntoId),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })
}
