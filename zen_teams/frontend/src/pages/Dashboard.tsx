import { useState, useEffect } from 'react'
import { Activity, Users, TicketCheck, Brain, Shield, Loader2 } from 'lucide-react'
import { api } from '../services/api'

interface Persona {
  id: string
  name: string
  icon: string
  role: string
  description: string
}

const roleColors: Record<string, string> = {
  pentester: 'bg-blue-900',
  analyst: 'bg-purple-900',
  researcher: 'bg-pink-900',
  ceo: 'bg-red-900',
}

export default function DashboardPage() {
  const [personas, setPersonas] = useState<Persona[]>([])
  const [agents, setAgents] = useState<any[]>([])
  const [tickets, setTickets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.getPersonas().catch(() => []),
      api.getAgents().catch(() => []),
      api.getTickets().catch(() => []),
    ])
      .then(([p, a, t]) => {
        setPersonas(p)
        setAgents(a)
        setTickets(t)
        setLoading(false)
      })
      .catch((e) => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

  const stats = [
    { label: 'Active Agents', value: String(agents.length || 11), icon: Users, color: 'text-blue-400' },
    { label: 'Open Tickets', value: String(tickets.filter((t) => t.status !== 'done').length || 0), icon: TicketCheck, color: 'text-yellow-400' },
    { label: 'Tasks Completed', value: String(tickets.filter((t) => t.status === 'done').length || 0), icon: Activity, color: 'text-green-400' },
    { label: 'Personas', value: String(personas.length || 11), icon: Brain, color: 'text-purple-400' },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-400" size={32} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="card border-red-500">
          <p className="text-red-400">Error loading data: {error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-400 mt-1">Overview of your AI security team</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.label} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">{stat.label}</p>
                <p className="text-2xl font-bold mt-1">{stat.value}</p>
              </div>
              <stat.icon className={stat.color} size={24} />
            </div>
          </div>
        ))}
      </div>

      {/* Personas Grid */}
      <div>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Brain size={20} />
          Available Personas ({personas.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {personas.map((persona) => (
            <div
              key={persona.id}
              className={`${roleColors[persona.role] || 'bg-gray-800'} rounded-xl p-4 border border-gray-700 hover:border-gray-500 transition-colors cursor-pointer`}
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">{persona.icon}</span>
                <div>
                  <h3 className="font-semibold">{persona.name}</h3>
                  <span className="badge badge-blue capitalize">{persona.role}</span>
                </div>
              </div>
              <p className="text-sm text-gray-300 mt-2 line-clamp-2">{persona.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Shield size={20} />
          Quick Actions
        </h2>
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary">Create Company</button>
          <button className="btn-primary">Hire Agent</button>
          <button className="btn-secondary">New Ticket</button>
          <button className="btn-secondary">Run Scan</button>
        </div>
      </div>
    </div>
  )
}
