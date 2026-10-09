/**
 * Estado global (Zustand + persistencia en localStorage):
 * punto de control, capa activa, años de análisis y estado del sidebar.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { LayerId } from '../types'

interface AppState {
  lat: number
  lon: number
  layer: LayerId
  years: number
  sidebarAbierto: boolean
  setPunto: (lat: number, lon: number) => void
  setCapa: (layer: LayerId) => void
  setAnios: (years: number) => void
  alternarSidebar: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      lat: -14.85,
      lon: -70.92,
      layer: 'biomasa',
      years: 20,
      sidebarAbierto: true,
      // Redondeo a 5 decimales (~1 m) para claves de caché estables
      setPunto: (lat, lon) => set({ lat: +lat.toFixed(5), lon: +lon.toFixed(5) }),
      setCapa: (layer) => set({ layer }),
      setAnios: (years) => set({ years }),
      alternarSidebar: () => set((s) => ({ sidebarAbierto: !s.sidebarAbierto })),
    }),
    {
      name: 'pacomarca-ui',
      // El estado del sidebar es de sesión, no se persiste
      partialize: (s) => ({ lat: s.lat, lon: s.lon, layer: s.layer, years: s.years }),
    },
  ),
)
