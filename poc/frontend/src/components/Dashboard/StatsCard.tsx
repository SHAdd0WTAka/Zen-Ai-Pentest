import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { motion } from 'framer-motion';

import { Severity } from '@/types';

// Utility for tailwind class merging
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface StatsCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  severity?: Severity;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  isLoading?: boolean;
  onClick?: () => void;
  className?: string;
}

const severityColors: Record<Severity, string> = {
  critical: 'bg-critical-500/10 text-critical-500 border-critical-500/20',
  high: 'bg-high-500/10 text-high-500 border-high-500/20',
  medium: 'bg-medium-500/10 text-medium-500 border-medium-500/20',
  low: 'bg-low-500/10 text-low-500 border-low-500/20',
  info: 'bg-brand-500/10 text-brand-500 border-brand-500/20',
};

const severityIconColors: Record<Severity, string> = {
  critical: 'bg-critical-500 text-white',
  high: 'bg-high-500 text-white',
  medium: 'bg-medium-500 text-white',
  low: 'bg-low-500 text-white',
  info: 'bg-brand-500 text-white',
};

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  severity = 'info',
  trend,
  isLoading = false,
  onClick,
  className,
}) => {
  if (isLoading) {
    return (
      <div
        className={cn(
          'relative overflow-hidden rounded-xl border border-dark-border bg-dark-card p-6',
          className
        )}
      >
        <div className="animate-pulse">
          <div className="flex items-center justify-between">
            <div className="h-4 w-24 rounded bg-dark-border" />
            <div className="h-10 w-10 rounded-lg bg-dark-border" />
          </div>
          <div className="mt-4 h-8 w-16 rounded bg-dark-border" />
          <div className="mt-2 h-3 w-32 rounded bg-dark-border" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-xl border border-dark-border bg-dark-card p-6 transition-all hover:border-brand-500/30 hover:shadow-lg hover:shadow-brand-500/5 cursor-pointer',
        className
      )}
    >
      {/* Background gradient */}
      <div
        className={cn(
          'absolute inset-0 opacity-0 transition-opacity group-hover:opacity-100',
          severityColors[severity]
        )}
      />

      <div className="relative">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-dark-muted">{title}</p>
            <h3 className="mt-2 text-3xl font-bold text-dark-text">{value}</h3>
            {subtitle && (
              <p className="mt-1 text-sm text-dark-muted">{subtitle}</p>
            )}
            {trend && (
              <div className="mt-2 flex items-center gap-1">
                <span
                  className={cn(
                    'text-xs font-medium',
                    trend.isPositive ? 'text-low-500' : 'text-critical-500'
                  )}
                >
                  {trend.isPositive ? '+' : ''}{trend.value}%
                </span>
                <span className="text-xs text-dark-muted">vs last week</span>
              </div>
            )}
          </div>

          <div
            className={cn(
              'flex h-12 w-12 items-center justify-center rounded-lg',
              severityIconColors[severity]
            )}
          >
            {icon}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default StatsCard;
