import { EvidenceList } from '@/components/evidence';
import { FileText, Shield } from 'lucide-react';

export function EvidencePanel() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Shield className="w-6 h-6 text-cyan-500" />
            Evidence Collection
          </h2>
          <p className="text-slate-500 mt-1">
            Tamper-proof evidence with chain of custody for legal proceedings
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <FileText className="w-4 h-4" />
          <span>Court-ready reports</span>
        </div>
      </div>

      {/* Evidence List */}
      <EvidenceList />
    </div>
  );
}
