import { useState, useEffect, useCallback } from 'react'
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState, type Node, type Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Network, Loader2 } from 'lucide-react'
import { api } from '../services/api'

const nodeColors: Record<string, string> = {
  ceo: '#dc2626',
  pentester: '#2563eb',
  analyst: '#9333ea',
  researcher: '#db2777',
}

export default function OrgChartPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [loading, setLoading] = useState(true)

  const buildChart = useCallback((personas: any[], agents: any[]) => {
    const newNodes: Node[] = []
    const newEdges: Edge[] = []

    // CEO / Red Team Lead at top
    const ceo = personas.find((p) => p.role === 'ceo')
    if (ceo) {
      newNodes.push({
        id: ceo.id,
        type: 'default',
        position: { x: 400, y: 0 },
        data: { label: `${ceo.icon} ${ceo.name}` },
        style: { background: nodeColors.ceo, color: '#fff', border: 'none', borderRadius: 8, padding: 10 },
      })
    }

    // Group personas by role
    const roles = ['pentester', 'analyst', 'researcher']
    let xOffset = 0
    roles.forEach((role) => {
      const rolePersonas = personas.filter((p) => p.role === role)
      rolePersonas.forEach((p, i) => {
        const y = 150 + i * 120
        const x = xOffset + i * 20
        newNodes.push({
          id: p.id,
          type: 'default',
          position: { x, y },
          data: { label: `${p.icon} ${p.name}` },
          style: { background: nodeColors[role] || '#374151', color: '#fff', border: 'none', borderRadius: 8, padding: 10 },
        })
        if (ceo) {
          newEdges.push({
            id: `${ceo.id}-${p.id}`,
            source: ceo.id,
            target: p.id,
            animated: true,
            style: { stroke: '#6b7280' },
          })
        }
      })
      xOffset += 250
    })

    // Add active agents as child nodes
    agents.forEach((agent, i) => {
      const parentId = agent.persona
      const parent = newNodes.find((n) => n.id === parentId)
      if (parent) {
        const agentId = `agent-${agent.id}`
        newNodes.push({
          id: agentId,
          type: 'default',
          position: { x: parent.position.x + (i % 2 === 0 ? -80 : 80), y: parent.position.y + 100 },
          data: { label: `🤖 ${agent.name}` },
          style: { background: '#059669', color: '#fff', border: 'none', borderRadius: 8, padding: 8, fontSize: 12 },
        })
        newEdges.push({
          id: `${parentId}-${agentId}`,
          source: parentId,
          target: agentId,
          style: { stroke: '#10b981' },
        })
      }
    })

    setNodes(newNodes)
    setEdges(newEdges)
  }, [setNodes, setEdges])

  useEffect(() => {
    Promise.all([api.getPersonas(), api.getAgents()])
      .then(([personas, agents]) => {
        buildChart(personas, agents)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [buildChart])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-400" size={32} />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-4 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Network size={28} />
          Team Org Chart
        </h1>
        <p className="text-gray-400 mt-1">Visual organization of your AI security team</p>
      </div>
      <div className="flex-1 card p-0 overflow-hidden min-h-[500px]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  )
}
