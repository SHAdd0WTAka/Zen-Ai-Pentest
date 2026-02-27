import { useState } from 'react';
import { ScanLine, Play, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

interface Scan {
  id: string;
  name: string;
  target: string;
  type: string;
  status: string;
  progress: number;
  findings: number;
  startTime: string;
}

export function ScanPanel({ scans }: { scans: Scan[] }) {
  const [activeScans, setActiveScans] = useState(scans);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <ScanLine className="w-5 h-5 text-slate-500" />;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <ScanLine className="w-5 h-5 text-cyan-500" />
          Active Scans
        </h2>
        <button className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-sm font-medium transition-colors">
          <Play className="w-4 h-4" />
          New Scan
        </button>
      </div>

      <div className="space-y-3">
        {activeScans.map((scan) => (
          <div
            key={scan.id}
            className="p-4 rounded-xl border border-slate-800 bg-slate-900/50"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                {getStatusIcon(scan.status)}
                <div>
                  <h3 className="font-medium text-slate-200">{scan.name}</h3>
                  <p className="text-sm text-slate-500">{scan.target}</p>
                  <p className="text-xs text-slate-600 mt-1">
                    Started: {new Date(scan.startTime).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-slate-200">
                  {scan.findings}
                </span>
                <p className="text-xs text-slate-500">findings</p>
              </div>
            </div>

            {scan.status === 'running' && (
              <div className="mt-4">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Progress</span>
                  <span className="text-cyan-400">{scan.progress}%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                    style={{ width: `${scan.progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
