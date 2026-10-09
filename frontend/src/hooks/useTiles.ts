/** URL de tiles XYZ de GEE para la capa activa. */
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import type { LayerId } from '../types'

export function useTiles(lat: number, lon: number, layer: LayerId) {
  return useQuery({
    queryKey: ['tiles', layer, lat.toFixed(2), lon.toFixed(2)],
    queryFn: () => api.tiles(layer, lat, lon),
    staleTime: 30 * 60 * 1000,
    retry: 1,
  })
}
