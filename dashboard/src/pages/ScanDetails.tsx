import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, RefreshCw } from 'lucide-react'
import { useScanStore } from '../store/scanStore'

export function ScanDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { currentScan, getScan, isLoading } = useScanStore()

  useEffect(() => {
    if (id) {
      getScan(id)
    }
  }, [id, getScan])

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-4 text-gray-500">Loading scan details...</p>
      </div>
    )
  }

  if (!currentScan) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Scan not found</p>
        <button
          onClick={() => navigate('/scans')}
          className="mt-4 text-primary-600 hover:underline"
        >
          Back to scans
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/scans')}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            <ArrowLeft className="h-6 w-6" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Scan: {currentScan.target}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={`badge ${
                currentScan.status === 'completed' ? 'badge-success' :
                currentScan.status === 'running' ? 'badge-info' :
                currentScan.status === 'failed' ? 'badge-danger' :
                'badge-warning'
              }`}>
                {currentScan.status}
              </span>
              <span className="text-sm text-gray-500">
                {currentScan.type}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary">
            <RefreshCw className="h-4 w-4 mr-2" />
            Re-run
          </button>
          <button className="btn-secondary">
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Summary */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Target</p>
              <p className="font-medium">{currentScan.target}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Type</p>
              <p className="font-medium capitalize">{currentScan.type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Created</p>
              <p className="font-medium">
                {new Date(currentScan.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Updated</p>
              <p className="font-medium">
                {new Date(currentScan.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Findings */}
        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Findings</h3>
          {currentScan.results ? (
            <pre className="bg-gray-50 rounded-lg p-4 overflow-auto text-sm">
              {JSON.stringify(currentScan.results, null, 2)}
            </pre>
          ) : (
            <p className="text-gray-500 text-center py-8">
              {currentScan.status === 'running'
                ? 'Scan in progress... Results will appear here.'
                : 'No results available yet.'}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}