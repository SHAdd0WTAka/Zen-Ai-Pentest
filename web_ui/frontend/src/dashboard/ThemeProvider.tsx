import { useEffect } from 'react';
import { useAgentStore } from '../store/agentStore';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useAgentStore();

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);

  return <>{children}</>;
}
