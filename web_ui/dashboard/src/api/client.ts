/**
 * API Client mit Authentication
 *
 * Zentrale Axios-Instanz die automatisch JWT Token sendet
 */
import axios from 'axios'

// API Base URL - empty string = use relative URLs (goes through Vite proxy)
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Axios Instance erstellen
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30s Timeout
})

// Request Interceptor - fügt Auth Header hinzu
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response Interceptor - handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login', { username, password })
    const { access_token } = response.data
    localStorage.setItem('access_token', access_token)
    return response.data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  },

  getToken: () => localStorage.getItem('access_token'),

  isAuthenticated: () => !!localStorage.getItem('access_token'),
}

// Dashboard API
export const dashboardApi = {
  getStats: () => apiClient.get('/api/v1/dashboard/stats'),
  getActiveScans: () => apiClient.get('/api/v1/dashboard/active-scans'),
  getRecentFindings: (limit = 10) => apiClient.get(`/api/v1/dashboard/recent-findings?limit=${limit}`),
  getActivities: () => apiClient.get('/api/v1/dashboard/activities'),
}

// Scans API
export const scansApi = {
  getAll: () => apiClient.get('/api/v1/scans-extended/'),
  getById: (id: number) => apiClient.get(`/api/v1/scans-extended/${id}/status`),
  create: (data: any) => apiClient.post('/api/v1/scans-extended/', data),
  createLegacy: (data: any) => apiClient.post('/scans', data),
  getLogs: (id: number, limit = 100) => apiClient.get(`/api/v1/scans-extended/${id}/logs?limit=${limit}`),
  getLogsLegacy: (id: number, limit = 100) => apiClient.get(`/scans/${id}/logs?limit=${limit}`),
  stop: (id: number) => apiClient.post(`/api/v1/scans-extended/${id}/action`, { action: 'stop' }),
  stopLegacy: (id: number) => apiClient.post(`/api/v1/scans/${id}/action`, { action: 'stop', reason: 'User requested' }),
  restart: (id: number) => apiClient.post(`/api/v1/scans-extended/${id}/action`, { action: 'restart' }),
}

// Findings API
export const findingsApi = {
  getAll: (params?: any) => apiClient.get('/scans/0/findings', { params }),
  update: (id: number, data: any) => apiClient.patch(`/findings/${id}`, data),
}

export default apiClient
