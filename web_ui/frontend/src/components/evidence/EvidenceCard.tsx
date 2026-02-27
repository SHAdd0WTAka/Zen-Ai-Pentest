import { useState } from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, Download, FileText, Image as ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Evidence {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  evidence_type: string;
  status: string;
  target: {
    url?: string;
    ip?: string;
    port?: number;
  };
  timestamps: {
    collected: string;
  };
  integrity: {
    verified: boolean;
    hash: string;
  };
  vulnerability_type?: string;
}

interface EvidenceCardProps {
  evidence: Evidence;
  onClick?: (evidence: Evidence) => void;
}

const severityConfig = {
  critical: { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/20', icon: AlertTriangle },
  high: { color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/20', icon: AlertTriangle },
  medium: { color: 'text-yellow-500', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', icon: AlertTriangle },
  low: { color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500/20', icon: CheckCircle },
  info: { color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500/20', icon: Info },
};

const typeIcons = {
  web_vulnerability: ImageIcon,
  api_vulnerability: FileText,
  network_vulnerability: Shield,
};

export function EvidenceCard({ evidence, onClick }: EvidenceCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  
  const severity = severityConfig[evidence.severity] || severityConfig.info;
  const TypeIcon = typeIcons[evidence.evidence_type as keyof typeof typeIcons] || FileText;
  const SeverityIcon = severity.icon;

  return (
    <div
      className={cn(
        'relative rounded-xl border p-4 transition-all duration-200 cursor-pointer',
        'bg-slate-900/50 backdrop-blur-sm',
        severity.border,
        isHovered && 'bg-slate-800/50 scale-[1.02]'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onClick?.(evidence)}
    >
      {/* Severity Indicator */}
      <div className={cn('absolute left-0 top-0 bottom-0 w-1 rounded-l-xl', severity.bg.replace('/10', ''))} />
      
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={cn('p-3 rounded-lg', severity.bg)}>
          <TypeIcon className={cn('w-5 h-5', severity.color)} />
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <SeverityIcon className={cn('w-4 h-4', severity.color)} />
            <span className={cn('text-xs font-semibold uppercase tracking-wider', severity.color)}>
              {evidence.severity}
            </span>
            <span className="text-xs text-slate-500">•</span>
            <span className="text-xs text-slate-500">{evidence.evidence_type.replace('_', ' ')}</span>
          </div>
          
          <h3 className="text-sm font-medium text-slate-200 truncate">
            {evidence.title}
          </h3>
          
          {evidence.target.url && (
            <p className="text-xs text-slate-500 mt-1 truncate">
              {evidence.target.url}
            </p>
          )}
          
          {evidence.target.ip && (
            <p className="text-xs text-slate-500 mt-1">
              {evidence.target.ip}{evidence.target.port ? `:${evidence.target.port}` : ''}
            </p>
          )}
          
          <div className="flex items-center gap-4 mt-3">
            {/* Collection Time */}
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5" />
              {new Date(evidence.timestamps.collected).toLocaleString()}
            </div>
            
            {/* Integrity Status */}
            <div className={cn(
              'flex items-center gap-1.5 text-xs',
              evidence.integrity.verified ? 'text-green-500' : 'text-red-500'
            )}>
              <Shield className="w-3.5 h-3.5" />
              {evidence.integrity.verified ? 'Verified' : 'Compromised'}
            </div>
          </div>
        </div>
        
        {/* Actions */}
        <div className={cn(
          'flex flex-col gap-2 transition-opacity duration-200',
          isHovered ? 'opacity-100' : 'opacity-0'
        )}>
          <button
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              // Download handler
            }}
            title="Download Evidence"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Hash Preview */}
      {evidence.integrity.hash && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <p className="text-[10px] text-slate-600 font-mono truncate">
            SHA-256: {evidence.integrity.hash}
          </p>
        </div>
      )}
    </div>
  );
}

function Info(props: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </svg>
  );
}
