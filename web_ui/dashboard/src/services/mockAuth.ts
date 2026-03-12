// ============================================
// Mock Authentication Service for Demo
// ============================================

import type { User } from '@/types';

const MOCK_USER: User = {
  id: '1',
  username: 'demo',
  email: 'demo@zen-ai-pentest.io',
  role: 'admin',
  createdAt: new Date().toISOString(),
  settings: {
    theme: 'dark',
    notifications: true,
    emailAlerts: true,
    scanDefaults: {
      intensity: 'normal',
      timeout: 3600,
      concurrentScans: 5,
    },
  },
};

class MockAuthService {
  private static instance: MockAuthService;
  private isAuthenticated = false;

  static getInstance(): MockAuthService {
    if (!MockAuthService.instance) {
      MockAuthService.instance = new MockAuthService();
    }
    return MockAuthService.instance;
  }

  login(username: string, password: string): Promise<{ user: User; access_token: string; refresh_token: string }> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        // Akzeptiere beliebige credentials für demo
        if (username && password) {
          this.isAuthenticated = true;
          localStorage.setItem('mock_auth', 'true');
          localStorage.setItem('mock_user', JSON.stringify(MOCK_USER));
          resolve({
            user: MOCK_USER,
            access_token: 'mock_token_' + Date.now(),
            refresh_token: 'mock_refresh_' + Date.now(),
          });
        } else {
          reject(new Error('Invalid credentials'));
        }
      }, 500);
    });
  }

  logout(): void {
    this.isAuthenticated = false;
    localStorage.removeItem('mock_auth');
    localStorage.removeItem('mock_user');
  }

  isLoggedIn(): boolean {
    return localStorage.getItem('mock_auth') === 'true';
  }

  getUser(): User | null {
    const user = localStorage.getItem('mock_user');
    return user ? JSON.parse(user) : null;
  }
}

export const mockAuth = MockAuthService.getInstance();
