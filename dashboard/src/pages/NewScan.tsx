import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Globe, Shield, Zap, Search } from 'lucide-react'
import { useScanStore } from '../store/scanStore'

const scanTypes = [
  {
    id: 'quick',
    name: 'Quick Scan',
    description: 'Fast reconnaissance with basic port scanning and technology detection',
    icon: Search,
    duration: '~2 minutes',
    color: 'blue',
  },
  {
    id: 'full',
    name: 'Full Scan',
    description: 'Comprehensive scan including all tools and vulnerability checks',
    icon: Shield,
    duration: '~10-15 minutes',
    color: 'green',
  },
  {
    id: 'super',
    name: 'Super Scan',
    description: 'Deep analysis with all OSINT and security tools',
    icon: Zap,
    duration: '~20-30 minutes',
    color: 'purple',
  },
]

export function NewScan() {
  const navigate = useNavigate()
  const { createScan, isLoading } = useScanStore()
  const [target, setTarget] = useState('')
  const [selectedType, setSelectedType] = useState('quick')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!target.trim()) {
      setError('Please enter a target')
      return
    }

    // Basic validation
    const targetRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$|^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
    if (!targetRegex.test(target) && !target.includes('.')) {
      setError('Please enter a valid domain or IP address')
      return
    }

    await createScan(target, selectedType)
    navigate('/scans')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/scans')}
          className="p-2 text-gray-400 hover:text-gray-600"
        >
          <ArrowLeft className="h-6 w-6" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">New Scan</h1>
          <p className="mt-1 text-sm text-gray-500">
            Configure and start a new security scan
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Target Input */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target
          </label>
          <div className="relative">
            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="example.com or 192.168.1.1"
              className="input pl-10"
            />
          </div>
          {error && (
            <p className="mt-2 text-sm text-danger-600">{error}</p>
          )}
          <p className="mt-2 text-sm text-gray-500">
            Enter a domain name or IP address to scan
          </p>
        </div>

        {/* Scan Type Selection */}
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Scan Type
          </label>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {scanTypes.map((type) => {
              const Icon = type.icon
              const isSelected = selectedType === type.id

              return (
                <div
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  className={`relative rounded-lg border p-4 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start">
                    <div className={`p-2 rounded-lg ${
                      type.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                      type.color === 'green' ? 'bg-green-100 text-green-600' :
                      'bg-purple-100 text-purple-600'
                    }`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div className="ml-3 flex-1">
                      <h3 className="text-sm font-medium text-gray-900">
                        {type.name}
                      </h3>
                      <p className="mt-1 text-xs text-gray-500">
                        {type.description}
                      </p>
                      <p className="mt-2 text-xs text-gray-400">
                        Duration: {type.duration}
                      </p>
                    </div>
                    {isSelected && (
                      <div className="absolute top-4 right-4">
                        <div className="h-5 w-5 rounded-full bg-primary-600 flex items-center justify-center">
                          <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/scans')}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary disabled:opacity-50"
          >
            {isLoading ? 'Starting Scan...' : 'Start Scan'}
          </button>
        </div>
      </form>
    </div>
  )
}