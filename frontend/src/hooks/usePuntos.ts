/**
 * Puntos de control guardados en la base de datos:
 * consulta reactiva + mutaciones con invalidación automática del caché.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import type { PuntoCreateInput } from '../types'

const CLAVE = ['puntos']

export function usePuntos() {
  return useQuery({
    queryKey: CLAVE,
    queryFn: () => api.puntos.listar(),
    staleTime: 60 * 1000,
    retry: 1,
  })
}

export function useCrearPunto() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: PuntoCreateInput) => api.puntos.crear(datos),
    onSuccess: () => cliente.invalidateQueries({ queryKey: CLAVE }),
  })
}

export function useActualizarPunto() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: ({ id, cambios }: { id: number; cambios: Partial<PuntoCreateInput> }) =>
      api.puntos.actualizar(id, cambios),
    onSuccess: () => cliente.invalidateQueries({ queryKey: CLAVE }),
  })
}

export function useEliminarPunto() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.puntos.eliminar(id),
    onSuccess: () => cliente.invalidateQueries({ queryKey: CLAVE }),
  })
}
