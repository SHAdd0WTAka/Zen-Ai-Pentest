// ============================================
// Loading Component
// ============================================

import React from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  fullscreen?: boolean;
}

const sizeMap = {
  sm: 'w-6 h-6',
  md: 'w-10 h-10',
  lg: 'w-16 h-16',
  xl: 'w-24 h-24',
};

export const LoadingSpinner: React.FC<LoadingProps> = ({
  size = 'md',
  text,
  fullscreen = false,
}) => {
  const spinner = (
    <div className="flex flex-col items-center gap-4">
      <div className={`relative ${sizeMap[size]}`}>
        <div className="absolute inset-0 border-2 border-gray-700 rounded-full" />
        <div className="absolute inset-0 border-2 border-cyan-500 rounded-full border-t-transparent animate-spin" />
      </div>
      {text && <p className="text-gray-400 text-sm">{text}</p>}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export const LoadingCard: React.FC<{ title?: string }> = ({ title }) => (
  <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 animate-pulse">
    {title && (
      <div className="h-6 bg-gray-700 rounded w-1/3 mb-4" />
    )}
    <div className="space-y-3">
      <div className="h-4 bg-gray-700 rounded w-full" />
      <div className="h-4 bg-gray-700 rounded w-5/6" />
      <div className="h-4 bg-gray-700 rounded w-4/6" />
    </div>
  </div>
);

export const LoadingTable: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4,
}) => (
  <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
    <div className="p-4 border-b border-gray-700">
      <div className="h-6 bg-gray-700 rounded w-1/4" />
    </div>
    <div className="divide-y divide-gray-700">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4 flex gap-4">
          {Array.from({ length: columns }).map((_, j) => (
            <div
              key={j}
              className="h-4 bg-gray-700 rounded animate-pulse"
              style={{ width: `${Math.random() * 20 + 15}%` }}
            />
          ))}
        </div>
      ))}
    </div>
  </div>
);

export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className = '',
}) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <div
        key={i}
        className="h-4 bg-gray-700 rounded animate-pulse"
        style={{
          width: i === lines - 1 ? '60%' : '100%',
          animationDelay: `${i * 100}ms`,
        }}
      />
    ))}
  </div>
);

export default LoadingSpinner;
