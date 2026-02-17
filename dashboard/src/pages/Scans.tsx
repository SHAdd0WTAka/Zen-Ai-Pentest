import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter, MoreVertical } from 'lucide-react'
import { useScanStore } from '../store/scanStore'

export function Scans() {
  const { scans, fetchScans, isLoading } = useScanStore()

  useEffect(() => {
    fetchScans()
  }, [fetchScans])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scans</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and monitor your security scans
          </p>
        </div>
        <Link to="/scans/new" className="btn-primary">
          <Plus className="h-5 w-5 mr-2" />
          New Scan
        </Link>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search scans..."
            className="input pl-10"
          />
        </div>
        <button className="btn-secondary">
          <Filter className="h-5 w-5 mr-2" />
          Filter
        </button>
      </div>

      {/* Scans Table */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading scans...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Target
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {scans.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      No scans yet. <Link to="/scans/new" className="text-primary-600 hover:underline">Create your first scan</Link>
                    </td>
                  </tr>
                ) : (
                  scans.map((scan) => (
                    <tr key={scan.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {scan.target}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-500 capitalize">
                          {scan.type}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`badge ${
                          scan.status === 'completed' ? 'badge-success' :
                          scan.status === 'running' ? 'badge-info' :
                          scan.status === 'failed' ? 'badge-danger' :
                          'badge-warning'
                        }`}>
                          {scan.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(scan.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/scans/${scan.id}`}
                          className="text-primary-600 hover:text-primary-700 font-medium"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}