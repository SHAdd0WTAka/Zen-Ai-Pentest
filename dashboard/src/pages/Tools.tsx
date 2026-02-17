import { 
  Search, 
  Globe, 
  Shield, 
  Terminal, 
  Network,
  Lock,
  Eye,
  FileSearch
} from 'lucide-react'

const toolCategories = [
  {
    name: 'Reconnaissance',
    tools: [
      { name: 'Subfinder', description: 'Subdomain discovery', icon: Globe, status: 'available' },
      { name: 'Amass', description: 'Advanced subdomain enumeration', icon: Network, status: 'available' },
      { name: 'WhatWeb', description: 'Technology detection', icon: Eye, status: 'available' },
      { name: 'Sherlock', description: 'Username OSINT', icon: Search, status: 'available' },
    ]
  },
  {
    name: 'Scanning',
    tools: [
      { name: 'Nmap', description: 'Port scanning', icon: Network, status: 'available' },
      { name: 'Nuclei', description: 'Vulnerability scanning', icon: Shield, status: 'available' },
      { name: 'Nikto', description: 'Web vulnerability scanner', icon: Lock, status: 'available' },
      { name: 'FFuF', description: 'Directory fuzzing', icon: FileSearch, status: 'available' },
    ]
  },
  {
    name: 'Network',
    tools: [
      { name: 'TShark', description: 'Network traffic analysis', icon: Network, status: 'available' },
      { name: 'HTTPX', description: 'HTTP prober', icon: Globe, status: 'available' },
    ]
  },
]

export function Tools() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tools</h1>
        <p className="mt-1 text-sm text-gray-500">
          Available security testing tools and their status
        </p>
      </div>

      {/* Tool Categories */}
      <div className="space-y-8">
        {toolCategories.map((category) => (
          <div key={category.name}>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{category.name}</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {category.tools.map((tool) => {
                const Icon = tool.icon
                return (
                  <div key={tool.name} className="card hover:shadow-md transition-shadow">
                    <div className="flex items-start">
                      <div className="p-2 bg-primary-100 rounded-lg">
                        <Icon className="h-6 w-6 text-primary-600" />
                      </div>
                      <div className="ml-3 flex-1">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-medium text-gray-900">{tool.name}</h3>
                          <span className={`badge ${
                            tool.status === 'available' ? 'badge-success' : 'badge-warning'
                          }`}>
                            {tool.status}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-gray-500">{tool.description}</p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Tool Stats */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Tool Statistics</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-3xl font-bold text-gray-900">15</p>
            <p className="text-sm text-gray-500">Total Tools</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-3xl font-bold text-green-600">14</p>
            <p className="text-sm text-gray-500">Available</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-3xl font-bold text-blue-600">11</p>
            <p className="text-sm text-gray-500">New Integrations</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-3xl font-bold text-purple-600">100%</p>
            <p className="text-sm text-gray-500">Async Support</p>
          </div>
        </div>
      </div>
    </div>
  )
}