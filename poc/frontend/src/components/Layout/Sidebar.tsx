import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import {
  ChartPieIcon,
  ShieldCheckIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  UsersIcon,
  BellIcon,
  BeakerIcon,
  CpuChipIcon,
  ArrowLeftOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

import { useAuthStore, useUIStore } from '@/store';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: ChartPieIcon },
  { name: 'Scans', href: '/scans', icon: MagnifyingGlassIcon },
  { name: 'Vulnerabilities', href: '/vulnerabilities', icon: ShieldCheckIcon },
  { name: 'Assets', href: '/assets', icon: CpuChipIcon },
  { name: 'Reports', href: '/reports', icon: DocumentTextIcon },
  { name: 'Agents', href: '/agents', icon: BeakerIcon },
  { name: 'Users', href: '/users', icon: UsersIcon },
  { name: 'Notifications', href: '/notifications', icon: BellIcon, badge: 3 },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { sidebarOpen } = useUIStore();
  const { logout, user } = useAuthStore();

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => useUIStore.getState().setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: sidebarOpen ? 280 : 80,
          x: sidebarOpen ? 0 : -200,
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className={cn(
          'fixed left-0 top-0 z-50 h-screen border-r border-dark-border bg-dark-bg',
          'lg:translate-x-0 lg:static lg:h-screen'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center border-b border-dark-border px-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700">
                <ShieldCheckIcon className="h-6 w-6 text-white" />
              </div>
              {sidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-lg font-bold text-dark-text whitespace-nowrap"
                >
                  Zen-AI-Pentest
                </motion.span>
              )}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                      isActive
                        ? 'bg-brand-500/10 text-brand-500'
                        : 'text-dark-muted hover:bg-dark-card hover:text-dark-text'
                    )
                  }
                >
                  <item.icon
                    className={cn(
                      'h-5 w-5 flex-shrink-0 transition-colors',
                      isActive
                        ? 'text-brand-500'
                        : 'text-dark-muted group-hover:text-dark-text'
                    )}
                  />
                  {sidebarOpen && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex-1 whitespace-nowrap"
                    >
                      {item.name}
                    </motion.span>
                  )}
                  {sidebarOpen && item.badge && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex h-5 w-5 items-center justify-center rounded-full bg-critical-500 text-xs font-bold text-white"
                    >
                      {item.badge}
                    </motion.span>
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* User section */}
          <div className="border-t border-dark-border p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold">
                {user?.fullName?.charAt(0) || 'U'}
              </div>
              {sidebarOpen && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 min-w-0"
                >
                  <p className="text-sm font-medium text-dark-text truncate">
                    {user?.fullName || 'User'}
                  </p>
                  <p className="text-xs text-dark-muted truncate">
                    {user?.email || 'user@example.com'}
                  </p>
                </motion.div>
              )}
              {sidebarOpen && (
                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={logout}
                  className="p-2 rounded-lg text-dark-muted hover:text-critical-500 hover:bg-critical-500/10 transition-colors"
                  title="Logout"
                >
                  <ArrowLeftOnRectangleIcon className="h-5 w-5" />
                </motion.button>
              )}
            </div>
          </div>
        </div>
      </motion.aside>
    </>
  );
};

export default Sidebar;
