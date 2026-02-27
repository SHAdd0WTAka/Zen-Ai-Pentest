import { useState } from 'react';
import { FileText, Download, Trash2, Clock, FileSpreadsheet, Shield, FileCode } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface Report {
  id: string;
  title: string;
  type: 'executive' | 'technical' | 'compliance';
  format: 'pdf' | 'html' | 'docx' | 'json';
  status: 'completed' | 'generating' | 'failed';
  company?: string;
  createdAt: string;
  size?: string;
}

const mockReports: Report[] = [
  {
    id: '1',
    title: 'Executive Summary - ACME Corp',
    type: 'executive',
    format: 'pdf',
    status: 'completed',
    company: 'ACME Corporation',
    createdAt: '2026-02-26T20:30:00Z',
    size: '2.4 MB',
  },
  {
    id: '2',
    title: 'Technical Report - Full Assessment',
    type: 'technical',
    format: 'pdf',
    status: 'completed',
    createdAt: '2026-02-26T19:15:00Z',
    size: '15.8 MB',
  },
  {
    id: '3',
    title: 'OWASP Compliance Assessment',
    type: 'compliance',
    format: 'html',
    status: 'completed',
    createdAt: '2026-02-26T18:45:00Z',
    size: '1.2 MB',
  },
  {
    id: '4',
    title: 'PCI DSS Compliance Report',
    type: 'compliance',
    format: 'pdf',
    status: 'generating',
    createdAt: '2026-02-26T20:45:00Z',
  },
];

const typeIcons = {
  executive: Shield,
  technical: FileCode,
  compliance: FileSpreadsheet,
};

const typeColors = {
  executive: 'text-purple-500',
  technical: 'text-cyan-500',
  compliance: 'text-green-500',
};

const formatIcons = {
  pdf: 'PDF',
  html: 'HTML',
  docx: 'DOCX',
  json: 'JSON',
};

export function ReportList() {
  const [reports, setReports] = useState<Report[]>(mockReports);

  const handleDelete = (id: string) => {
    setReports(reports.filter(r => r.id !== id));
  };

  return (
    <div className="space-y-4">
      {reports.map((report) => {
        const TypeIcon = typeIcons[report.type];
        
        return (
          <Card key={report.id} className="border-slate-800 bg-slate-900/50">
            <CardContent className="p-4">
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className={cn('p-3 rounded-lg bg-slate-800/50')}>
                  <TypeIcon className={cn('w-5 h-5', typeColors[report.type])} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-slate-200 truncate">
                      {report.title}
                    </h3>
                    <span className={cn(
                      'px-2 py-0.5 rounded text-xs font-medium',
                      report.status === 'completed' && 'bg-green-500/10 text-green-500',
                      report.status === 'generating' && 'bg-yellow-500/10 text-yellow-500',
                      report.status === 'failed' && 'bg-red-500/10 text-red-500',
                    )}>
                      {report.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="px-2 py-0.5 rounded bg-slate-800 font-medium">
                      {formatIcons[report.format]}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(report.createdAt).toLocaleString()}
                    </span>
                    {report.size && (
                      <span>{report.size}</span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {report.status === 'completed' && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-slate-400 hover:text-cyan-500"
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-400 hover:text-red-500"
                    onClick={() => handleDelete(report.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Progress bar for generating */}
              {report.status === 'generating' && (
                <div className="mt-4">
                  <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-yellow-500 animate-pulse w-2/3" />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}

      {reports.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 mx-auto text-slate-700 mb-4" />
          <p className="text-slate-500">No reports generated yet</p>
        </div>
      )}
    </div>
  );
}
