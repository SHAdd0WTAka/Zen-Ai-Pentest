import { Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Evidence {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  integrity: {
    verified: boolean;
  };
}

interface EvidenceStatsProps {
  evidence: Evidence[];
}

export function EvidenceStats({ evidence }: EvidenceStatsProps) {
  const stats = {
    total: evidence.length,
    critical: evidence.filter(e => e.severity === 'critical').length,
    high: evidence.filter(e => e.severity === 'high').length,
    medium: evidence.filter(e => e.severity === 'medium').length,
    verified: evidence.filter(e => e.integrity.verified).length,
  };

  const cards = [
    {
      label: 'Total Evidence',
      value: stats.total,
      icon: Shield,
      color: 'text-cyan-500',
      bg: 'bg-cyan-500/10',
    },
    {
      label: 'Critical',
      value: stats.critical,
      icon: AlertTriangle,
      color: 'text-red-500',
      bg: 'bg-red-500/10',
    },
    {
      label: 'High Severity',
      value: stats.high,
      icon: AlertTriangle,
      color: 'text-orange-500',
      bg: 'bg-orange-500/10',
    },
    {
      label: 'Verified',
      value: stats.verified,
      icon: CheckCircle,
      color: 'text-green-500',
      bg: 'bg-green-500/10',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <div
          key={index}
          className={cn(
            'rounded-xl border border-slate-800 p-4',
            'bg-slate-900/50 backdrop-blur-sm',
            'hover:bg-slate-800/50 transition-colors'
          )}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">
                {card.label}
              </p>
              <p className={cn('text-2xl font-bold mt-1', card.color)}>
                {card.value}
              </p>
            </div>
            <div className={cn('p-2 rounded-lg', card.bg)}>
              <card.icon className={cn('w-5 h-5', card.color)} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
