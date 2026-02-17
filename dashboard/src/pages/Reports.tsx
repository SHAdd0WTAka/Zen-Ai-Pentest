import { Download, FileText, FileJson, FileCode } from 'lucide-react'

const reportTypes = [
  {
    name: 'PDF Report',
    description: 'Professional PDF report with findings and recommendations',
    icon: FileText,
    format: 'pdf',
    color: 'red',
  },
  {
    name: 'JSON Export',
    description: 'Machine-readable JSON format for integration',
    icon: FileCode,
    format: 'json',
    color: 'blue',
  },
  {
    name: 'HTML Report',
    description: 'Interactive HTML report for browser viewing',
    icon: FileText,
    format: 'html',
    color: 'orange',
  },
  {
    name: 'Markdown',
    description: 'Markdown format for documentation',
    icon: FileText,
    format: 'md',
    color: 'gray',
  },
]

const recentReports = [
  { id: 1, name: 'example.com_scan_report.pdf', target: 'example.com', date: '2024-01-15', size: '2.4 MB' },
  { id: 2, name: 'test.com_findings.json', target: 'test.com', date: '2024-01-14', size: '156 KB' },
  { id: 3, name: 'demo.org_full_scan.html', target: 'demo.org', date: '2024-01-13', size: '4.1 MB' },
]

export function Reports() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="mt-1 text-sm text-gray-500">
          Generate and download scan reports
        </p>
      </div>

      {/* Report Types */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {reportTypes.map((type) => {
          const Icon = type.icon
          return (
            <div key={type.name} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start">
                <div className={`p-3 rounded-lg ${
                  type.color === 'red' ? 'bg-red-100' :
                  type.color === 'blue' ? 'bg-blue-100' :
                  type.color === 'orange' ? 'bg-orange-100' :
                  'bg-gray-100'
                }`}>
                  <Icon className={`h-6 w-6 ${
                    type.color === 'red' ? 'text-red-600' :
                    type.color === 'blue' ? 'text-blue-600' :
                    type.color === 'orange' ? 'text-orange-600' :
                    'text-gray-600'
                  }`} />
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-gray-900">{type.name}</h3>
                  <p className="mt-1 text-xs text-gray-500">{type.description}</p>
                  <button className="mt-3 text-xs text-primary-600 hover:text-primary-700 font-medium">
                    Generate
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Reports */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Reports</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {recentReports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{report.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{report.target}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{report.date}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{report.size}</td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-primary-600 hover:text-primary-700">
                      <Download className="h-5 w-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}