import { useEffect, useRef, useState } from 'react';
import {
  Shield,
  Terminal,
  GitBranch,
  Star,
  Package,
  Activity,
} from 'lucide-react';
import { getStats, type SystemStats } from '@/lib/api';

const defaultStats = [
  {
    icon: Shield,
    value: 40,
    suffix: '+',
    label: 'Security Tools',
    description: 'Integrated professional tools',
    color: 'from-cyan-500 to-blue-500',
    apiKey: null,
  },
  {
    icon: Star,
    value: 205,
    suffix: '+',
    label: 'GitHub Stars',
    description: 'Community support',
    color: 'from-yellow-500 to-orange-500',
    apiKey: null,
  },
  {
    icon: GitBranch,
    value: 780,
    suffix: '+',
    label: 'Commits',
    description: 'Active development',
    color: 'from-purple-500 to-pink-500',
    apiKey: null,
  },
  {
    icon: Activity,
    value: 0,
    suffix: '',
    label: 'Total Scans',
    description: 'Completed security scans',
    color: 'from-green-500 to-emerald-500',
    apiKey: 'total_scans',
  },
  {
    icon: Package,
    value: 0,
    suffix: '',
    label: 'Findings',
    description: 'Vulnerabilities detected',
    color: 'from-red-500 to-rose-500',
    apiKey: 'total_findings',
  },
  {
    icon: Terminal,
    value: 100,
    suffix: '%',
    label: 'Real Execution',
    description: 'No mocks, real tools',
    color: 'from-indigo-500 to-violet-500',
    apiKey: null,
  },
];

function AnimatedCounter({ value, suffix }: { value: number; suffix: string }) {
  const [count, setCount] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.5 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isVisible) return;

    const duration = 2000;
    const steps = 60;
    const increment = value / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [isVisible, value]);

  return (
    <span ref={ref}>
      {count}
      {suffix}
    </span>
  );
}

export function Stats() {
  const [stats, setStats] = useState(defaultStats);
  const [apiConnected, setApiConnected] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      const apiStats = await getStats();
      if (apiStats) {
        setApiConnected(true);
        setStats(prev => prev.map(stat => {
          if (stat.apiKey && apiStats[stat.apiKey as keyof SystemStats] !== undefined) {
            return { ...stat, value: apiStats[stat.apiKey as keyof SystemStats] as number };
          }
          return stat;
        }));
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative py-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900/50 to-slate-950" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Trusted by Security Professionals
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Join the growing community of security researchers and penetration testers
            using Zen-AI-Pentest for autonomous vulnerability assessments.
          </p>
          {apiConnected && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-medium mt-4">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live Data
            </span>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="group relative p-6 rounded-xl bg-slate-900/50 border border-slate-800/50 hover:border-slate-700/50 transition-all duration-300 hover:scale-105"
            >
              {/* Glow Effect */}
              <div
                className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity duration-300`}
              />

              {/* Icon */}
              <div
                className={`inline-flex p-3 rounded-lg bg-gradient-to-br ${stat.color} mb-4`}
              >
                <stat.icon className="w-6 h-6 text-white" />
              </div>

              {/* Value */}
              <div className="text-3xl font-bold text-white mb-1">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
              </div>

              {/* Label */}
              <div className="text-sm font-medium text-slate-300 mb-1">
                {stat.label}
              </div>

              {/* Description */}
              <div className="text-xs text-slate-500">{stat.description}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
