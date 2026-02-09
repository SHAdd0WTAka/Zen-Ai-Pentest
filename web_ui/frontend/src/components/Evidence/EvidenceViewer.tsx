// ============================================
// Evidence Viewer Component
// ============================================

import React, { useState, useRef, useCallback } from 'react';
import { Evidence, EvidenceType } from '../../types';
import { formatBytes, formatDate } from '../../utils/formatters';

interface EvidenceViewerProps {
  evidence: Evidence[];
  onDownload?: (evidence: Evidence) => void;
  onDelete?: (id: string) => void;
}

type ViewMode = 'gallery' | 'list' | 'detail';

// Screenshot Gallery Component
const ScreenshotGallery: React.FC<{
  items: Evidence[];
  onSelect: (item: Evidence) => void;
  onDownload: (item: Evidence) => void;
}> = ({ items, onSelect, onDownload }) => {
  const [selectedImage, setSelectedImage] = useState<Evidence | null>(null);
  const [zoom, setZoom] = useState(1);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {items.map((item) => (
          <div
            key={item.id}
            className="group relative bg-gray-900 rounded-lg overflow-hidden border border-gray-700 hover:border-cyan-500 transition-colors cursor-pointer"
            onClick={() => {
              setSelectedImage(item);
              onSelect(item);
            }}
          >
            <div className="aspect-video bg-gray-800 flex items-center justify-center">
              {item.metadata?.url ? (
                <img
                  src={item.metadata.url}
                  alt={item.metadata.filename || 'Screenshot'}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="text-4xl">🖼️</div>
              )}
            </div>
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDownload(item);
                }}
                className="p-2 bg-cyan-600 rounded-lg text-white hover:bg-cyan-500"
                aria-label="Herunterladen"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
            </div>
            <div className="p-2">
              <p className="text-sm text-gray-300 truncate">{item.metadata.filename || 'Screenshot'}</p>
              <p className="text-xs text-gray-500">{formatDate(item.createdAt)}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center"
          onClick={() => {
            setSelectedImage(null);
            setZoom(1);
          }}
        >
          <div className="absolute top-4 right-4 flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleZoomOut();
              }}
              className="p-2 bg-gray-800 rounded-lg text-white hover:bg-gray-700"
              aria-label="Verkleinern"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleResetZoom();
              }}
              className="px-3 py-2 bg-gray-800 rounded-lg text-white hover:bg-gray-700 text-sm"
            >
              {Math.round(zoom * 100)}%
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleZoomIn();
              }}
              className="p-2 bg-gray-800 rounded-lg text-white hover:bg-gray-700"
              aria-label="Vergrößern"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDownload(selectedImage);
              }}
              className="p-2 bg-cyan-600 rounded-lg text-white hover:bg-cyan-500"
              aria-label="Herunterladen"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedImage(null);
                setZoom(1);
              }}
              className="p-2 bg-gray-800 rounded-lg text-white hover:bg-gray-700"
              aria-label="Schließen"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {selectedImage.metadata?.url && (
            <img
              src={selectedImage.metadata.url}
              alt={selectedImage.metadata.filename || 'Screenshot'}
              className="max-w-full max-h-full transition-transform"
              style={{ transform: `scale(${zoom})` }}
              onClick={(e) => e.stopPropagation()}
            />
          )}
        </div>
      )}
    </>
  );
};

// HTTP Response Viewer Component
const HttpResponseViewer: React.FC<{ evidence: Evidence }> = ({ evidence }) => {
  const [viewMode, setViewMode] = useState<'parsed' | 'raw'>('parsed');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(evidence.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  let parsedContent: unknown = null;
  let isJson = false;
  try {
    parsedContent = JSON.parse(evidence.content);
    isJson = true;
  } catch {
    // Not JSON, treat as raw
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
      <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center gap-4">
          <h4 className="text-white font-medium">{evidence.metadata.filename || 'HTTP Response'}</h4>
          {isJson && (
            <div className="flex bg-gray-700 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('parsed')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === 'parsed' ? 'bg-cyan-600 text-white' : 'text-gray-400'
                }`}
              >
                Parsed
              </button>
              <button
                onClick={() => setViewMode('raw')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === 'raw' ? 'bg-cyan-600 text-white' : 'text-gray-400'
                }`}
              >
                Raw
              </button>
            </div>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-white transition-colors"
        >
          {copied ? (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Kopiert
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Kopieren
            </>
          )}
        </button>
      </div>
      <div className="p-4 overflow-auto max-h-96">
        {viewMode === 'parsed' && isJson ? (
          <pre className="text-sm text-green-400 font-mono">
            {JSON.stringify(parsedContent, null, 2)}
          </pre>
        ) : (
          <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
            {evidence.content}
          </pre>
        )}
      </div>
    </div>
  );
};

// Video Player Component
const VideoPlayer: React.FC<{ evidence: Evidence }> = ({ evidence }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
      <video
        ref={videoRef}
        src={evidence.metadata?.url}
        className="w-full aspect-video bg-black"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
      />
      <div className="p-3 bg-gray-800 flex items-center gap-4">
        <button
          onClick={togglePlay}
          className="w-10 h-10 bg-cyan-600 hover:bg-cyan-500 rounded-full flex items-center justify-center text-white transition-colors"
        >
          {isPlaying ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
        <div className="flex-1">
          <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-cyan-500 transition-all"
              style={{ width: `${(currentTime / duration) * 100}%` }}
            />
          </div>
        </div>
        <span className="text-sm text-gray-400 font-mono">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>
    </div>
  );
};

// PCAP Player Component
const PcapPlayer: React.FC<{ evidence: Evidence }> = ({ evidence }) => {
  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 p-6">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-16 h-16 bg-blue-900/50 rounded-lg flex items-center justify-center text-3xl">
          📡
        </div>
        <div>
          <h4 className="text-white font-medium">{evidence.metadata.filename || 'PCAP File'}</h4>
          <p className="text-gray-400 text-sm">{formatBytes(evidence.metadata.size || 0)}</p>
          <p className="text-gray-500 text-xs">{formatDate(evidence.createdAt)}</p>
        </div>
      </div>
      <div className="bg-gray-800 rounded-lg p-4 mb-4">
        <p className="text-gray-400 text-sm">
          PCAP-Dateien können mit Wireshark oder tcpdump analysiert werden.
        </p>
      </div>
      <div className="flex gap-2">
        <a
          href={evidence.metadata?.url}
          download={evidence.metadata.filename}
          className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-center transition-colors"
        >
          Download
        </a>
      </div>
    </div>
  );
};

// Main Evidence Viewer Component
const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  evidence,
  onDownload,
  onDelete,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('gallery');
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [filter, setFilter] = useState<EvidenceType | 'all'>('all');

  const filteredEvidence = evidence.filter(
    (e) => filter === 'all' || e.type === filter
  );

  const groupedEvidence = filteredEvidence.reduce((acc, item) => {
    if (!acc[item.type]) acc[item.type] = [];
    acc[item.type].push(item);
    return acc;
  }, {} as Record<EvidenceType, Evidence[]>);

  const handleDownload = useCallback(
    (item: Evidence) => {
      onDownload?.(item);
      // Fallback: trigger download if URL is available
      if (item.metadata?.url && !onDownload) {
        const link = document.createElement('a');
        link.href = item.metadata.url;
        link.download = item.metadata.filename || 'download';
        link.click();
      }
    },
    [onDownload]
  );

  const typeIcons: Record<EvidenceType, string> = {
    screenshot: '🖼️',
    http_response: '🌐',
    pcap: '📡',
    video: '🎬',
    log: '📄',
    file: '📎',
  };

  const typeLabels: Record<EvidenceType, string> = {
    screenshot: 'Screenshots',
    http_response: 'HTTP Responses',
    pcap: 'PCAP Files',
    video: 'Videos',
    log: 'Logs',
    file: 'Files',
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 border-b border-gray-700">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-white">Evidence</h3>
          <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded-full text-sm">
            {evidence.length} Items
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as EvidenceType | 'all')}
            className="bg-gray-700 text-white rounded-lg px-3 py-1.5 text-sm border border-gray-600 focus:border-cyan-500 focus:outline-none"
          >
            <option value="all">Alle Typen</option>
            {Object.entries(typeLabels).map(([type, label]) => (
              <option key={type} value={type}>
                {typeIcons[type as EvidenceType]} {label}
              </option>
            ))}
          </select>

          {/* View Mode Toggle */}
          <div className="flex bg-gray-700 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('gallery')}
              className={`p-2 rounded ${viewMode === 'gallery' ? 'bg-cyan-600 text-white' : 'text-gray-400'}`}
              aria-label="Galerie-Ansicht"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-cyan-600 text-white' : 'text-gray-400'}`}
              aria-label="Listen-Ansicht"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {viewMode === 'gallery' ? (
          <div className="space-y-6">
            {(['screenshot', 'video', 'pcap', 'http_response', 'log', 'file'] as EvidenceType[]).map(
              (type) => {
                const items = groupedEvidence[type];
                if (!items || items.length === 0) return null;

                return (
                  <div key={type}>
                    <h4 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                      <span>{typeIcons[type]}</span>
                      {typeLabels[type]} ({items.length})
                    </h4>
                    {type === 'screenshot' && (
                      <ScreenshotGallery
                        items={items}
                        onSelect={setSelectedEvidence}
                        onDownload={handleDownload}
                      />
                    )}
                    {type === 'video' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {items.map((item) => (
                          <VideoPlayer key={item.id} evidence={item} />
                        ))}
                      </div>
                    )}
                    {type === 'pcap' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {items.map((item) => (
                          <PcapPlayer key={item.id} evidence={item} />
                        ))}
                      </div>
                    )}
                    {type === 'http_response' && (
                      <div className="space-y-4">
                        {items.map((item) => (
                          <HttpResponseViewer key={item.id} evidence={item} />
                        ))}
                      </div>
                    )}
                    {(type === 'log' || type === 'file') && (
                      <div className="bg-gray-900 rounded-lg border border-gray-700 divide-y divide-gray-700">
                        {items.map((item) => (
                          <div
                            key={item.id}
                            className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-2xl">{typeIcons[type]}</span>
                              <div>
                                <p className="text-white text-sm">{item.metadata.filename || 'File'}</p>
                                <p className="text-gray-500 text-xs">
                                  {formatBytes(item.metadata.size || 0)} • {formatDate(item.createdAt)}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleDownload(item)}
                                className="p-2 text-gray-400 hover:text-white transition-colors"
                                aria-label="Herunterladen"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                              </button>
                              {onDelete && (
                                <button
                                  onClick={() => onDelete(item.id)}
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
                        ))}
                      </div>
                    )}
                  </div>
                );
              }
            )}
          </div>
        ) : (
          // List View
          <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Typ</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Größe</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Datum</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Aktionen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredEvidence.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-800 transition-colors">
                    <td className="px-4 py-3">
                      <span className="text-xl">{typeIcons[item.type]}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-white text-sm">{item.metadata.filename || 'Unnamed'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-gray-400 text-sm">{formatBytes(item.metadata.size || 0)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-gray-400 text-sm">{formatDate(item.createdAt)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setSelectedEvidence(item)}
                          className="p-1.5 text-gray-400 hover:text-white transition-colors"
                          aria-label="Anzeigen"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDownload(item)}
                          className="p-1.5 text-gray-400 hover:text-white transition-colors"
                          aria-label="Herunterladen"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </button>
                        {onDelete && (
                          <button
                            onClick={() => onDelete(item.id)}
                            className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
                            aria-label="Löschen"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {filteredEvidence.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-3">📂</div>
            <p className="text-gray-400">Keine Evidence-Daten vorhanden</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidenceViewer;
