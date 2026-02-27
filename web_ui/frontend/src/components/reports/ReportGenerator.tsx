import { useState } from 'react';
import { FileText, Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  formats: string[];
}

const templates: ReportTemplate[] = [
  {
    id: 'executive',
    name: 'Executive Summary',
    description: 'High-level report for C-level executives with risk overview and strategic recommendations',
    formats: ['pdf', 'html', 'docx'],
  },
  {
    id: 'technical',
    name: 'Technical Report',
    description: 'Detailed technical findings for IT and security teams with evidence and remediation',
    formats: ['pdf', 'html', 'docx', 'json'],
  },
  {
    id: 'compliance',
    name: 'Compliance Assessment',
    description: 'Compliance-focused report mapping findings to frameworks (OWASP, ISO 27001, PCI DSS)',
    formats: ['pdf', 'html', 'json'],
  },
];

const complianceFrameworks = [
  { id: 'owasp', name: 'OWASP Top 10 (2021)' },
  { id: 'iso27001', name: 'ISO 27001:2022' },
  { id: 'pci_dss', name: 'PCI DSS 4.0' },
  { id: 'nist', name: 'NIST CSF 2.0' },
];

export function ReportGenerator() {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('executive');
  const [selectedFormat, setSelectedFormat] = useState<string>('pdf');
  const [companyName, setCompanyName] = useState('');
  const [selectedFramework, setSelectedFramework] = useState('owasp');
  const [isGenerating, setIsGenerating] = useState(false);

  const template = templates.find(t => t.id === selectedTemplate);

  const handleGenerate = async () => {
    setIsGenerating(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsGenerating(false);
    alert('Report generated successfully!');
  };

  return (
    <div className="space-y-6">
      {/* Template Selection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {templates.map((t) => (
          <Card
            key={t.id}
            className={cn(
              'cursor-pointer transition-all',
              selectedTemplate === t.id
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-slate-800 hover:border-slate-700'
            )}
            onClick={() => {
              setSelectedTemplate(t.id);
              setSelectedFormat(t.formats[0]);
            }}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-500" />
                {t.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500">{t.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Configuration */}
      <Card className="border-slate-800">
        <CardHeader>
          <CardTitle className="text-lg">Report Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Company Name */}
          <div className="space-y-2">
            <Label htmlFor="company">Company Name</Label>
            <Input
              id="company"
              placeholder="ACME Corporation"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="bg-slate-900/50 border-slate-800"
            />
          </div>

          {/* Compliance Framework (only for compliance report) */}
          {selectedTemplate === 'compliance' && (
            <div className="space-y-2">
              <Label>Compliance Framework</Label>
              <select
                value={selectedFramework}
                onChange={(e) => setSelectedFramework(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-slate-900/50 border border-slate-800 text-sm"
              >
                {complianceFrameworks.map((f) => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Format Selection */}
          <div className="space-y-2">
            <Label>Export Format</Label>
            <div className="flex gap-2">
              {template?.formats.map((format) => (
                <button
                  key={format}
                  onClick={() => setSelectedFormat(format)}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    selectedFormat === format
                      ? 'bg-cyan-500 text-white'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  )}
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Options */}
          {selectedTemplate === 'technical' && (
            <div className="flex gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked className="rounded border-slate-700" />
                <span className="text-slate-400">Include Evidence Screenshots</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked className="rounded border-slate-700" />
                <span className="text-slate-400">Include Remediation Steps</span>
              </label>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generate Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleGenerate}
          disabled={isGenerating || !companyName}
          className="bg-cyan-500 hover:bg-cyan-600 text-white gap-2"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              Generate Report
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
