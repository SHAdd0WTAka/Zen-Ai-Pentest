import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Layout } from '../Layout'

// Mock the auth store
vi.mock('../../store/authStore', () => ({
  useAuthStore: () => ({
    user: { username: 'testuser', role: 'admin' },
    logout: vi.fn(),
  }),
}))

describe('Layout Component', () => {
  it('renders sidebar navigation', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </BrowserRouter>
    )

    expect(screen.getByText('Zen-AI')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Scans')).toBeInTheDocument()
  })

  it('renders user info in header', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </BrowserRouter>
    )

    expect(screen.getByText('testuser')).toBeInTheDocument()
  })
})
