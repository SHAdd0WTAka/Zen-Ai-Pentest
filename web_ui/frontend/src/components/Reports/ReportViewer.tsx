// ============================================
// Report Viewer Component
// ============================================

import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Report } from '../../types';
import { formatDate, formatBytes } from '../../utils/formatters';

interface ReportViewerProps {
  report: Report;
  onDownload?: (report: Report) => void;
  onDelete?: (id: string) => void;
}

type ViewMode = 'markdown' | 'html' | 'pdf' | 'json';

// JSON Tree View Component
const JsonTreeView: React.FC<{ data: unknown; level?: number }> = ({ data, level = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(level < 2);

  if (data === null) return <span className="text-gray-500">null</span>;
  if (typeof data === 'boolean') return <span className="text-orange-400">{String(data)}</span>;
  if (typeof data === 'number') return <span className="text-cyan-400">{data}</span>;
  if (typeof data === 'string') return <span className="text-green-400">"{data}"</span>;

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-gray-500">[]</span>;
    return (
      <div style={{ marginLeft: level > 0 ? 20 : 0 }}>
        <span
          className="cursor-pointer text-gray-400 hover:text-white"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼' : '▶'} [{data.length}]
        </span>
        {isExpanded && (
          <div className="ml-4 border-l border-gray-700 pl-2">
            {data.map((item, index) => (
              <div key={index}>
                <span className="text-gray-500">{index}:</span>{' '}
                <JsonTreeView data={item} level={level + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) return <span className="text-gray-500">{'{}'}</span>;
    return (
      <div style={{ marginLeft: level > 0 ? 20 : 0 }}>
        <span
          className="cursor-pointer text-gray-400 hover:text-white"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼' : '▶'} {'{'} {entries.length} keys {'}'}
        </span>
        {isExpanded && (
          <div className="ml-4 border-l border-gray-700 pl-2">
            {entries.map(([key, value]) => (
              <div key={key}>
                <span className="text-purple-400">"{key}"</span>
                <span className="text-gray-500">: </span>
                <JsonTreeView data={value} level={level + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return <span className="text-gray-500">{String(data)}</span>;
};

// HTML Preview Component
const HtmlPreview: React.FC<{ content: string }> = ({ content }) => {
  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Report</title>
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }
              h1, h2, h3 { color: #333; }
              pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
              code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
              table { border-collapse: collapse; width: 100%; margin: 15px 0; }
              th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
              th { background: #f4f4f4; }
              .severity-critical { color: #dc2626; }
              .severity-high { color: #ea580c; }
              .severity-medium { color: #ca8a04; }
              .severity-low { color: #2563eb; }
            </style>
          </head>
          <body>
            ${content}
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          onClick={handlePrint}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Drucken
        </button>
      </div>
      <div
        className="prose prose-invert max-w-none bg-gray-900 p-6 rounded-lg border border-gray-700"
        dangerouslySetInnerHTML={{ __html: content }}
      />
    </div>
  );
};

// PDF Viewer Component
const PdfViewer: React.FC<{ url: string }> = ({ url }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
      <div className="flex items-center justify-between p-3 bg-gray-800 border-b border-gray-700">
        <span className="text-white font-medium">PDF Vorschau</span>
        <a
          href={url}
          download
          className="flex items-center gap-2 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-sm rounded-lg transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download
        </a>
      </div>
      <div className="h-[600px]">
        {loading && (
          <div className="h-full flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
          </div>
        )}
        {error && (
          <div className="h-full flex items-center justify-center text-red-400">
            <p>Fehler beim Laden des PDFs: {error}</p>
          </div>
        )}
        <iframe
          src={url}
          className="w-full h-full"
          onLoad={() => setLoading(false)}
          onError={() => {
            setLoading(false);
            setError('PDF konnte nicht geladen werden');
          }}
          title="PDF Viewer"
        />
      </div>
    </div>
  );
};

// Main Report Viewer Component
const ReportViewer: React.FC<ReportViewerProps> = ({ report, onDownload, onDelete }) => {
  const [viewMode, setViewMode] = useState<ViewMode>(report.format as ViewMode || 'markdown');
  const [content, setContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  // Fetch report content
  useEffect(() => {
    const fetchContent = async () => {
      if (report.status !== 'completed') return;
      
      setIsLoading(true);
      try {
        if (report.format === 'json') {
          const response = await fetch(report.url || '');
          const data = await response.json();
          setContent(JSON.stringify(data, null, 2));
        } else if (report.content) {
          setContent(report.content);
        } else if (report.url) {
          const response = await fetch(report.url);
          const text = await response.text();
          setContent(text);
        }
      } catch (error) {
        console.error('Failed to load report:', error);
        setContent('Fehler beim Laden des Reports');
      } finally {
        setIsLoading(false);
      }
    };

    fetchContent();
  }, [report]);

  const handleDownload = useCallback(() => {
    onDownload?.(report);
    if (report.url && !onDownload) {
      const link = document.createElement('a');
      link.href = report.url;
      link.download = `${report.name}.${report.format}`;
      link.click();
    }
  }, [report, onDownload]);

  const formatIcons: Record<ViewMode, string> = {
    markdown: '📝',
    html: '🌐',
    pdf: '📄',
    json: '📋',
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
        </div>
      );
    }

    if (report.status === 'generating') {
      return (
        <div className="flex items-center justify-center h-64 text-gray-400">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4" />
            <p>Report wird generiert...</p>
          </div>
        </div>
      );
    }

    if (report.status === 'failed') {
      return (
        <div className="flex items-center justify-center h-64 text-red-400">
          <div className="text-center">
            <div className="text-4xl mb-4">❌</div>
            <p>Report-Generierung fehlgeschlagen</p>
          </div>
        </div>
      );
    }

    switch (viewMode) {
      case 'markdown':
        return (
          <div className="prose prose-invert max-w-none bg-gray-900 p-6 rounded-lg border border-gray-700">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        );

      case 'html':
        return <HtmlPreview content={content} />;

      case 'pdf':
        return report.url ? (
          <PdfViewer url={report.url} />
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-400">
            <p>PDF nicht verfügbar</p>
          </div>
        );

      case 'json':
        try {
          const jsonData = JSON.parse(content);
          return (
            <div className="bg-gray-900 p-6 rounded-lg border border-gray-700 font-mono text-sm overflow-auto max-h-[600px]">
              <JsonTreeView data={jsonData} />
            </div>
          );
        } catch {
          return (
            <div className="bg-gray-900 p-6 rounded-lg border border-gray-700">
              <pre className="text-gray-300 font-mono text-sm whitespace-pre-wrap">{content}</pre>
            </div>
          );
        }

      default:
        return null;
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-semibold text-white">{report.name}</h3>
            <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
              <span>Format: <span className="text-gray-300 uppercase">{report.format}</span></span>
              <span>•</span>
              <span>Größe: {formatBytes(report.size || 0)}</span>
              <span>•</span>
              <span>Erstellt: {formatDate(report.createdAt)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex bg-gray-700 rounded-lg p-0.5">
              {(['markdown', 'html', 'pdf', 'json'] as ViewMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  disabled={report.format !== mode && report.format !== 'markdown'}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    viewMode === mode
                      ? 'bg-cyan-600 text-white'
                      : 'text-gray-400 hover:text-white disabled:opacity-30'
                  }`}
                >
                  {formatIcons[mode]} {mode.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>

            {/* Delete Button */}
            {onDelete && (
              <button
                onClick={() => {
                  if (confirm('Möchten Sie diesen Report wirklich löschen?')) {
                    onDelete(report.id);
                  }
                }}
                className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                aria-label="Löschen"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Status Badge */}
      <div className="px-4 py-2 bg-gray-900/50 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-sm">Status:</span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              report.status === 'completed'
                ? 'bg-green-900/50 text-green-400'
                : report.status === 'generating'
                ? 'bg-yellow-900/50 text-yellow-400'
                : 'bg-red-900/50 text-red-400'
            }`}
          >
            {report.status === 'completed'
              ? '✅ Abgeschlossen'
              : report.status === 'generating'
              ? '⏳ Wird generiert...'
              : '❌ Fehlgeschlagen'}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {renderContent()}
      </div>
    </div>
  );
};

export default ReportViewer;
