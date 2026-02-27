import { useState } from 'react';
import { FileText, Download, Shield, FileCode, FileSpreadsheet, Loader2 } from 'lucide-react';

const templates = [
  {
    id: 'executive',
    name: 'Executive Summary',
    description: 'High-level report for C-level executives',
    icon: Shield,
    formats: ['pdf', 'html', 'docx'],
  },
  {
    id: 'technical',
    name: 'Technical Report',
    description: 'Detailed findings for IT and security teams',
    icon: FileCode,
    formats: ['pdf', 'html', 'docx', 'json'],
  },
  {
    id: 'compliance',
    name: 'Compliance Assessment',
    description: 'Compliance mapping report',
    icon: FileSpreadsheet,
    formats: ['pdf', 'html', 'json'],
  },
];

export function ReportPanel() {
  const [selectedTemplate, setSelectedTemplate] = useState(templates[0]);
  const [selectedFormat, setSelectedFormat] = useState('pdf');
  const [companyName, setCompanyName] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!companyName) return;
    setIsGenerating(true);
    // Simulate generation
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsGenerating(false);
    alert(`Report generated successfully!\n\nType: ${selectedTemplate.name}\nFormat: ${selectedFormat.toUpperCase()}\nCompany: ${companyName}`);
  };

  return (
    <div className="space-y-6">
      {/* Template Selection */}
      <div className="grid grid-cols-3 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            onClick={() => {
              setSelectedTemplate(template);
              setSelectedFormat(template.formats[0]);
            }}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              selectedTemplate.id === template.id
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-slate-800">
                <template.icon className="w-5 h-5 text-cyan-500" />
              </div>
              <h3 className="font-medium text-slate-200">{template.name}</h3>
            </div>
            <p className="text-sm text-slate-500">{template.description}</p>
          </div>
        ))}
      </div>

      {/* Configuration */}
      <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/50">
        <h3 className="text-lg font-semibold mb-4">Report Configuration</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Company Name</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="ACME Corporation"
              className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Export Format</label>
            <div className="flex gap-2">
              {selectedTemplate.formats.map((format) => (
                <button
                  key={format}
                  onClick={() => setSelectedFormat(format)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedFormat === format
                      ? 'bg-cyan-500 text-white'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isGenerating || !companyName}
            className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-800 disabled:text-slate-500 rounded-lg font-medium transition-colors"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating Report...
              </>
            ) : (
              <>
                <Download className="w-5 h-5" />
                Generate Report
              </>
            )}
          </button>
        </div>
      </div>

      {/* Recent Reports */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Recent Reports</h3>
        <div className="space-y-3">
          {[
            { id: 1, name: 'Executive Summary - Demo Corp', type: 'executive', date: '2026-02-26', size: '2.4 MB' },
            { id: 2, name: 'Technical Assessment Report', type: 'technical', date: '2026-02-25', size: '15.8 MB' },
          ].map((report) => (
            <div
              key={report.id}
              className="flex items-center justify-between p-4 rounded-xl border border-slate-800 bg-slate-900/50"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-slate-500" />
                <div>
                  <h4 className="font-medium text-slate-200">{report.name}</h4>
                  <p className="text-sm text-slate-500">{report.date} • {report.size}</p>
                </div>
              </div>
              <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                <Download className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
