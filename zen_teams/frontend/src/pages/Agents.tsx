import { useState, useEffect } from 'react'
import { Users, Plus, Play, Pause, Power, Loader2 } from 'lucide-react'
import { api } from '../services/api'

const statusColors: Record<string, string> = {
  active: 'badge-green',
  paused: 'badge-yellow',
  busy: 'badge-blue',
  terminated: 'badge-red',
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getAgents()
      .then((data) => {
        setAgents(data.length ? data : [])
        setLoading(false)
      })
      .catch((e) => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-400" size={32} />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users size={28} />
            Agents
          </h1>
          <p className="text-gray-400 mt-1">Manage your AI security team</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus size={18} />
          Hire Agent
        </button>
      </div>

      {error && (
        <div className="card border-red-500">
          <p className="text-red-400">Error: {error}</p>
        </div>
      )}

      <div className="space-y-3">
        {agents.length === 0 && !error && (
          <div className="card text-center py-12">
            <p className="text-gray-400">No agents hired yet. Create your first AI security agent!</p>
            <button className="btn-primary mt-4">Hire Agent</button>
          </div>
        )}
        {agents.map((agent) => (
          <div key={agent.id} className="card flex items-center justify-between hover:border-gray-500 transition-colors">
            <div className="flex items-center gap-4">
              <span className="text-4xl">{agent.meta_data?.avatar || agent.avatar || '🤖'}</span>
              <div>
                <h3 className="font-semibold text-lg">{agent.name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`badge ${statusColors[agent.status] || 'badge-gray'}`}>
                    {agent.status}
                  </span>
                  <span className="text-sm text-gray-400">{agent.persona}</span>
                  <span className="text-sm text-gray-500">• {agent.tasks || 0} tasks</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors" title="Run">
                <Play size={18} className="text-green-400" />
              </button>
              <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors" title="Pause">
                <Pause size={18} className="text-yellow-400" />
              </button>
              <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors" title="Stop">
                <Power size={18} className="text-red-400" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
