import { create } from 'zustand'

interface Scan {
  id: string
  target: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  type: string
  created_at: string
  updated_at: string
  results?: any
}

interface ScanState {
  scans: Scan[]
  currentScan: Scan | null
  isLoading: boolean
  error: string | null
  fetchScans: () => Promise<void>
  createScan: (target: string, type: string) => Promise<void>
  getScan: (id: string) => Promise<void>
}

export const useScanStore = create<ScanState>((set, get) => ({
  scans: [],
  currentScan: null,
  isLoading: false,
  error: null,

  fetchScans: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/scans')
      if (!response.ok) throw new Error('Failed to fetch scans')
      const data = await response.json()
      set({ scans: data, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },

  createScan: async (target: string, type: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/scans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, type }),
      })
      if (!response.ok) throw new Error('Failed to create scan')
      const data = await response.json()
      set((state) => ({ 
        scans: [data, ...state.scans],
        isLoading: false 
      }))
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },

  getScan: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/scans/${id}`)
      if (!response.ok) throw new Error('Failed to fetch scan')
      const data = await response.json()
      set({ currentScan: data, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },
}))