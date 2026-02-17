import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuthStore } from '../authStore'

// Mock fetch
global.fetch = vi.fn()

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })
  
  it('has correct initial state', () => {
    const state = useAuthStore.getState()
    
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
  
  it('login sets user on success', async () => {
    const mockResponse = {
      user: { id: '1', username: 'admin', email: 'admin@test.com', role: 'admin' },
      access_token: 'test_token',
    }
    
    ;(fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })
    
    const result = await useAuthStore.getState().login('admin', 'admin')
    
    expect(result).toBe(true)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().user?.username).toBe('admin')
  })
  
  it('login returns false on failure', async () => {
    ;(fetch as any).mockResolvedValueOnce({
      ok: false,
    })
    
    const result = await useAuthStore.getState().login('wrong', 'wrong')
    
    expect(result).toBe(false)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
  
  it('logout clears state', () => {
    // Set authenticated state first
    useAuthStore.setState({
      user: { id: '1', username: 'admin', email: 'admin@test.com', role: 'admin' },
      token: 'test_token',
      isAuthenticated: true,
    })
    
    useAuthStore.getState().logout()
    
    expect(useAuthStore.getState().user).toBeNull()
    expect(useAuthStore.getState().token).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})
