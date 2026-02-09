// ============================================
// Findings Table Component with Filtering
// ============================================

import React, { useState, useMemo, useCallback } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { Finding, SeverityLevel, FindingStatus, ConfidenceLevel } from '../../types';
import {
  useFindings,
  useBulkUpdateFindings,
  useBulkDeleteFindings,
  useExportFindings,
  useUpdateFindingNotes,
} from '../../hooks/useFindings';
import {
  severityColors,
  severityLabels,
  findingStatusColors,
  findingStatusLabels,
  confidenceColors,
  formatDate,
  formatRelativeTime,
  getRiskScoreColor,
} from '../../utils/formatters';
import { LoadingTable } from '../Loading';

interface FindingsTableProps {
  scanId?: string;
  onFindingClick?: (finding: Finding) => void;
}

// Severity Badge Component
const SeverityBadge: React.FC<{ severity: SeverityLevel }> = ({ severity }) => {
  const colors = severityColors[severity];
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text} border ${colors.border}`}
    >
      {severityLabels[severity]}
    </span>
  );
};

// Status Badge Component
const StatusBadge: React.FC<{ status: FindingStatus }> = ({ status }) => {
  const colors = findingStatusColors[status];
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
      {findingStatusLabels[status]}
    </span>
  );
};

// Risk Score Component
const RiskScore: React.FC<{ score: number }> = ({ score }) => {
  const colorClass = getRiskScoreColor(score);
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${getRiskScoreColor(score).replace('text-', 'bg-')}`}
          style={{ width: `${Math.min(score * 10, 100)}%` }}
        />
      </div>
      <span className={`text-sm font-medium ${colorClass}`}>{score.toFixed(1)}</span>
    </div>
  );
};

// Filter Dropdown Component
interface FilterDropdownProps {
  label: string;
  options: { value: string; label: string }[];
  value: string[];
  onChange: (values: string[]) => void;
}

const FilterDropdown: React.FC<FilterDropdownProps> = ({ label, options, value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleValue = (v: string) => {
    if (value.includes(v)) {
      onChange(value.filter((x) => x !== v));
    } else {
      onChange([...value, v]);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
      >
        {label}
        {value.length > 0 && (
          <span className="bg-cyan-600 text-white text-xs px-1.5 py-0.5 rounded-full">
            {value.length}
          </span>
        )}
        <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-20 min-w-48 p-2">
            {options.map((option) => (
              <label
                key={option.value}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-700 rounded cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={value.includes(option.value)}
                  onChange={() => toggleValue(option.value)}
                  className="rounded border-gray-600 text-cyan-600 focus:ring-cyan-500"
                />
                <span className="text-white text-sm">{option.label}</span>
              </label>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// Editable Notes Cell
const EditableNotes: React.FC<{ finding: Finding; onSave: (notes: string) => void }> = ({
  finding,
  onSave,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [notes, setNotes] = useState(finding.notes || '');

  const handleSave = () => {
    onSave(notes);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          onBlur={handleSave}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSave();
            if (e.key === 'Escape') {
              setNotes(finding.notes || '');
              setIsEditing(false);
            }
          }}
          className="flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm focus:border-cyan-500 focus:outline-none"
          autoFocus
        />
        <button onClick={handleSave} className="text-green-400 hover:text-green-300">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div
      className="flex items-center gap-2 group cursor-pointer"
      onClick={() => setIsEditing(true)}
    >
      <span className="text-gray-300 text-sm truncate max-w-xs">
        {finding.notes || <span className="text-gray-500 italic">Klicken zum Bearbeiten...</span>}
      </span>
      <button className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white transition-opacity">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
        </svg>
      </button>
    </div>
  );
};

// Main Findings Table Component
const FindingsTable: React.FC<FindingsTableProps> = ({ scanId, onFindingClick }) => {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'riskScore', desc: true }]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [severityFilter, setSeverityFilter] = useState<SeverityLevel[]>([]);
  const [statusFilter, setStatusFilter] = useState<FindingStatus[]>([]);
  const [confidenceFilter, setConfidenceFilter] = useState<ConfidenceLevel[]>([]);

  // Fetch findings
  const { data: findingsData, isLoading } = useFindings({
    scanId,
    page: 1,
    perPage: 100,
  });

  const findings = findingsData?.items || [];

  // Mutations
  const bulkUpdateMutation = useBulkUpdateFindings();
  const bulkDeleteMutation = useBulkDeleteFindings();
  const exportMutation = useExportFindings();
  const updateNotesMutation = useUpdateFindingNotes();

  // Filter findings
  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (severityFilter.length > 0 && !severityFilter.includes(f.severity)) return false;
      if (statusFilter.length > 0 && !statusFilter.includes(f.status)) return false;
      if (confidenceFilter.length > 0 && !confidenceFilter.includes(f.confidence)) return false;
      if (globalFilter) {
        const search = globalFilter.toLowerCase();
        return (
          f.title.toLowerCase().includes(search) ||
          f.description.toLowerCase().includes(search) ||
          f.target.toLowerCase().includes(search)
        );
      }
      return true;
    });
  }, [findings, severityFilter, statusFilter, confidenceFilter, globalFilter]);

  // Handlers
  const toggleSelectAll = useCallback(() => {
    if (selectedRows.size === filteredFindings.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(filteredFindings.map((f) => f.id)));
    }
  }, [selectedRows, filteredFindings]);

  const toggleSelectRow = useCallback((id: string) => {
    setSelectedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleBulkStatusUpdate = (status: FindingStatus) => {
    bulkUpdateMutation.mutate({
      ids: Array.from(selectedRows),
      data: { status },
    });
    setSelectedRows(new Set());
  };

  const handleBulkDelete = () => {
    if (confirm(`Möchten Sie ${selectedRows.size} Findings wirklich löschen?`)) {
      bulkDeleteMutation.mutate(Array.from(selectedRows));
      setSelectedRows(new Set());
    }
  };

  const handleBulkExport = (format: 'json' | 'csv' | 'xml') => {
    exportMutation.mutate({
      ids: Array.from(selectedRows),
      format,
    });
  };

  const handleBulkFalsePositive = () => {
    bulkUpdateMutation.mutate({
      ids: Array.from(selectedRows),
      data: { isFalsePositive: true, status: 'false_positive' },
    });
    setSelectedRows(new Set());
  };

  if (isLoading) {
    return <LoadingTable rows={10} columns={8} />;
  }

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      {/* Toolbar */}
      <div className="p-4 border-b border-gray-700 space-y-4">
        {/* Search and Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-64">
            <input
              type="text"
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              placeholder="Findings durchsuchen..."
              className="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 focus:border-cyan-500 focus:outline-none"
            />
            <svg className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <FilterDropdown
            label="Schweregrad"
            options={Object.entries(severityLabels).map(([k, v]) => ({ value: k, label: v }))}
            value={severityFilter}
            onChange={(v) => setSeverityFilter(v as SeverityLevel[])}
          />

          <FilterDropdown
            label="Status"
            options={Object.entries(findingStatusLabels).map(([k, v]) => ({ value: k, label: v }))}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v as FindingStatus[])}
          />

          <FilterDropdown
            label="Confidence"
            options={[
              { value: 'confirmed', label: 'Bestätigt' },
              { value: 'high', label: 'Hoch' },
              { value: 'medium', label: 'Mittel' },
              { value: 'low', label: 'Niedrig' },
            ]}
            value={confidenceFilter}
            onChange={(v) => setConfidenceFilter(v as ConfidenceLevel[])}
          />
        </div>

        {/* Bulk Actions */}
        {selectedRows.size > 0 && (
          <div className="flex flex-wrap items-center gap-2 p-3 bg-cyan-900/30 border border-cyan-700/50 rounded-lg">
            <span className="text-cyan-400 text-sm font-medium">
              {selectedRows.size} ausgewählt
            </span>
            <div className="h-4 w-px bg-cyan-700 mx-2" />
            <button
              onClick={() => handleBulkStatusUpdate('validated')}
              className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white text-sm rounded-lg transition-colors"
            >
              Validieren
            </button>
            <button
              onClick={() => handleBulkStatusUpdate('resolved')}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
            >
              Als behoben markieren
            </button>
            <button
              onClick={handleBulkFalsePositive}
              className="px-3 py-1.5 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded-lg transition-colors"
            >
              Falsch positiv
            </button>
            <div className="h-4 w-px bg-cyan-700 mx-2" />
            <button
              onClick={() => handleBulkExport('json')}
              className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
            >
              Export JSON
            </button>
            <button
              onClick={() => handleBulkExport('csv')}
              className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
            >
              Export CSV
            </button>
            <button
              onClick={handleBulkDelete}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-sm rounded-lg transition-colors ml-auto"
            >
              Löschen
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-900/50">
            <tr>
              <th className="px-4 py-3 w-12">
                <input
                  type="checkbox"
                  checked={selectedRows.size === filteredFindings.length && filteredFindings.length > 0}
                  onChange={toggleSelectAll}
                  className="rounded border-gray-600 text-cyan-600 focus:ring-cyan-500"
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
                  onClick={() => setSorting([{ id: 'severity', desc: !sorting[0]?.desc }])}>
                <div className="flex items-center gap-1">
                  Schweregrad
                  {sorting[0]?.id === 'severity' && (
                    <span>{sorting[0].desc ? '↓' : '↑'}</span>
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Titel
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Ziel
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
                  onClick={() => setSorting([{ id: 'riskScore', desc: !sorting[0]?.desc }])}>
                <div className="flex items-center gap-1">
                  Risk Score
                  {sorting[0]?.id === 'riskScore' && (
                    <span>{sorting[0].desc ? '↓' : '↑'}</span>
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Notizen
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
                  onClick={() => setSorting([{ id: 'createdAt', desc: !sorting[0]?.desc }])}>
                <div className="flex items-center gap-1">
                  Datum
                  {sorting[0]?.id === 'createdAt' && (
                    <span>{sorting[0].desc ? '↓' : '↑'}</span>
                  )}
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {filteredFindings
              .sort((a, b) => {
                const sort = sorting[0];
                if (!sort) return 0;
                
                const aVal = a[sort.id as keyof Finding];
                const bVal = b[sort.id as keyof Finding];
                
                if (typeof aVal === 'number' && typeof bVal === 'number') {
                  return sort.desc ? bVal - aVal : aVal - bVal;
                }
                
                const comparison = String(aVal).localeCompare(String(bVal));
                return sort.desc ? -comparison : comparison;
              })
              .map((finding) => (
                <tr
                  key={finding.id}
                  className="hover:bg-gray-700/50 transition-colors cursor-pointer"
                  onClick={() => onFindingClick?.(finding)}
                >
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedRows.has(finding.id)}
                      onChange={() => toggleSelectRow(finding.id)}
                      className="rounded border-gray-600 text-cyan-600 focus:ring-cyan-500"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={finding.severity} />
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-white font-medium text-sm">{finding.title}</p>
                      <p className="text-gray-500 text-xs truncate max-w-xs">{finding.description}</p>
                      {finding.cveIds && finding.cveIds.length > 0 && (
                        <div className="flex gap-1 mt-1">
                          {finding.cveIds.slice(0, 3).map((cve) => (
                            <span key={cve} className="text-xs text-red-400 bg-red-900/30 px-1.5 py-0.5 rounded">
                              {cve}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-gray-300 text-sm">{finding.target}</span>
                    {finding.port && (
                      <span className="text-gray-500 text-xs ml-2">:{finding.port}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <RiskScore score={finding.riskScore} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={finding.status} />
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <EditableNotes
                      finding={finding}
                      onSave={(notes) => updateNotesMutation.mutate({ id: finding.id, notes })}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-gray-400 text-sm">
                      {formatRelativeTime(finding.createdAt)}
                    </span>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {filteredFindings.length === 0 && (
        <div className="text-center py-12">
          <div className="text-4xl mb-3">🔍</div>
          <p className="text-gray-400">Keine Findings gefunden</p>
        </div>
      )}

      {/* Pagination Info */}
      <div className="px-4 py-3 border-t border-gray-700 flex items-center justify-between text-sm text-gray-400">
        <span>
          Zeige {filteredFindings.length} von {findings.length} Findings
        </span>
      </div>
    </div>
  );
};

export default FindingsTable;
