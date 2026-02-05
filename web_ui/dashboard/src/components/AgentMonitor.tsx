import { useState, useEffect, useRef } from 'react'
import { 
  Bot, 
  Activity, 
  Brain,
  MessageSquare,
  Play,
  Pause,
  Square,
  Zap,
  Clock,
  Terminal,
  Users,
  Wifi,
  WifiOff
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Types
interface Agent {
  id: string
  name: string
  role: string
  state: 'idle' | 'thinking' | 'executing' | 'waiting' | 'completed' | 'failed' | 'stopped'
  current_task: string | null
  task_progress: number
  memory_entries: number
  queue_size: number
  connected_since: string
  last_activity: string
  current_tool: string | null
  scan_id: number | null
}

interface AgentThought {
  id: string
  agent_id: string
  timestamp: string
  thought_type: 'reasoning' | 'observation' | 'action' | 'reflection' | 'conclusion'
  content: string
  confidence: number | null
  related_tool: string | null
  metadata: Record<string, any>
}

interface AgentAction {
  id: string
  agent_id: string
  timestamp: string
  action_type: string
  target: string | null
  parameters: Record<string, any>
  result: string | null
  duration_ms: number | null
  success: boolean | null
}

const STATE_COLORS: Record<string, { bg: string; text: string; icon: React.ElementType }> = {
  idle: { bg: 'bg-slate-500/20', text: 'text-slate-400', icon: Bot },
  thinking: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: Brain },
  executing: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: Zap },
  waiting: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: Clock },
  completed: { bg: 'bg-green-500/20', text: 'text-green-400', icon: Activity },
  failed: { bg: 'bg-red-500/20', text: 'text-red-400', icon: Activity },
  stopped: { bg: 'bg-gray-500/20', text: 'text-gray-400', icon: Square },
}

const ROLE_ICONS: Record<string, React.ElementType> = {
  researcher: Bot,
  analyst: Brain,
  exploit: Zap,
  coordinator: Users,
  reporter: MessageSquare,
  post_exploitation: Activity,
}

// Agent Card Component
function AgentCard({ 
  agent, 
  isSelected, 
  onClick 
}: { 
  agent: Agent
  isSelected: boolean
  onClick: () => void 
}) {
  const stateConfig = STATE_COLORS[agent.state] || STATE_COLORS.idle
  const RoleIcon = ROLE_ICONS[agent.role] || Bot
  const StateIcon = stateConfig.icon

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-4 rounded-xl border transition-all duration-200',
        isSelected
          ? 'bg-blue-500/10 border-blue-500/50 ring-1 ring-blue-500/50'
          : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', stateConfig.bg)}>
            <RoleIcon className={cn('w-5 h-5', stateConfig.text)} />
          </div>
          <div>
            <h4 className="font-medium text-slate-200">{agent.name}</h4>
            <p className="text-sm text-slate-500 capitalize">{agent.role.replace('_', ' ')}</p>
          </div>
        </div>
        <div className={cn('px-2 py-1 rounded-full text-xs font-medium border', stateConfig.bg, stateConfig.text, 'border-current opacity-50')}>
          {agent.state}
        </div>
      </div>

      {agent.current_task && (
        <div className="mt-3">
          <p className="text-sm text-slate-400 truncate">{agent.current_task}</p>
          <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className={cn('h-full rounded-full transition-all duration-500', stateConfig.text.replace('text-', 'bg-'))}
              style={{ width: `${agent.task_progress}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <Brain className="w-3 h-3" />
          {agent.memory_entries} memories
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatDistanceToNow(new Date(agent.last_activity), { addSuffix: true })}
        </span>
      </div>
    </button>
  )
}

// Thought Stream Component
function ThoughtStream({ 
  thoughts, 
  agentId 
}: { 
  thoughts: AgentThought[]
  agentId: string 
}) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [thoughts])

  const getThoughtIcon = (type: string) => {
    switch (type) {
      case 'reasoning': return <Brain className="w-4 h-4 text-purple-400" />
      case 'observation': return <Activity className="w-4 h-4 text-blue-400" />
      case 'action': return <Zap className="w-4 h-4 text-yellow-400" />
      case 'reflection': return <Clock className="w-4 h-4 text-slate-400" />
      case 'conclusion': return <Terminal className="w-4 h-4 text-green-400" />
      default: return <MessageSquare className="w-4 h-4 text-slate-400" />
    }
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-auto space-y-3 p-4 font-mono text-sm">
      {thoughts.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          <Brain className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No thoughts recorded yet...</p>
        </div>
      ) : (
        thoughts.map((thought) => (
          <div 
            key={thought.id}
            className="flex gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 animate-fade-in"
          >
            <div className="shrink-0 mt-0.5">
              {getThoughtIcon(thought.thought_type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-slate-500 uppercase font-bold">{thought.thought_type}</span>
                <span className="text-xs text-slate-600">
                  {formatDistanceToNow(new Date(thought.timestamp), { addSuffix: true })}
                </span>
                {thought.confidence !== null && (
                  <span className={cn(
                    'text-xs px-1.5 py-0.5 rounded',
                    thought.confidence > 0.8 ? 'bg-green-500/20 text-green-400' :
                    thought.confidence > 0.5 ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-red-500/20 text-red-400'
                  )}>
                    {Math.round(thought.confidence * 100)}%
                  </span>
                )}
              </div>
              <p className="text-slate-300 leading-relaxed">{thought.content}</p>
              {thought.related_tool && (
                <div className="mt-2 flex items-center gap-2">
                  <Zap className="w-3 h-3 text-slate-500" />
                  <span className="text-xs text-slate-500">{thought.related_tool}</span>
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  )
}

// Action Log Component
function ActionLog({ actions }: { actions: AgentAction[] }) {
  return (
    <div className="flex-1 overflow-auto space-y-2 p-4 font-mono text-sm">
      {actions.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          <Terminal className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No actions recorded yet...</p>
        </div>
      ) : (
        actions.map((action) => (
          <div 
            key={action.id}
            className={cn(
              'flex items-start gap-3 p-3 rounded-lg border',
              action.success === true ? 'bg-green-500/5 border-green-500/20' :
              action.success === false ? 'bg-red-500/5 border-red-500/20' :
              'bg-slate-800/50 border-slate-700/50'
            )}
          >
            <div className={cn(
              'w-2 h-2 rounded-full mt-1.5 shrink-0',
              action.success === true ? 'bg-green-500' :
              action.success === false ? 'bg-red-500' :
              'bg-yellow-500 animate-pulse'
            )} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-300">{action.action_type}</span>
                {action.duration_ms && (
                  <span className="text-xs text-slate-500">({action.duration_ms}ms)</span>
                )}
              </div>
              {action.target && (
                <p className="text-slate-400 text-xs mt-1">Target: {action.target}</p>
              )}
              {Object.keys(action.parameters).length > 0 && (
                <pre className="mt-2 text-xs text-slate-500 bg-slate-900/50 p-2 rounded overflow-auto">
                  {JSON.stringify(action.parameters, null, 2)}
                </pre>
              )}
              {action.result && (
                <p className={cn(
                  'mt-2 text-xs',
                  action.success ? 'text-green-400' : 'text-red-400'
                )}>
                  {action.result}
                </p>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  )
}

// Main Component
export default function AgentMonitor() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [thoughts, setThoughts] = useState<AgentThought[]>([])
  const [actions, setActions] = useState<AgentAction[]>([])
  const [wsConnected, setWsConnected] = useState(false)
  const [activeTab, setActiveTab] = useState<'thoughts' | 'actions'>('thoughts')
  const wsRef = useRef<WebSocket | null>(null)

  // Mock agents for demonstration
  useEffect(() => {
    const mockAgents: Agent[] = [
      {
        id: 'agent-001',
        name: 'Recon Agent Alpha',
        role: 'researcher',
        state: 'executing',
        current_task: 'Performing subdomain enumeration',
        task_progress: 65,
        memory_entries: 42,
        queue_size: 3,
        connected_since: new Date(Date.now() - 3600000).toISOString(),
        last_activity: new Date().toISOString(),
        current_tool: 'amass',
        scan_id: 1
      },
      {
        id: 'agent-002',
        name: 'Vuln Scanner Beta',
        role: 'analyst',
        state: 'thinking',
        current_task: 'Analyzing port scan results',
        task_progress: 30,
        memory_entries: 28,
        queue_size: 1,
        connected_since: new Date(Date.now() - 7200000).toISOString(),
        last_activity: new Date(Date.now() - 30000).toISOString(),
        current_tool: null,
        scan_id: 1
      },
      {
        id: 'agent-003',
        name: 'Exploit Agent Gamma',
        role: 'exploit',
        state: 'waiting',
        current_task: 'Waiting for vulnerability confirmation',
        task_progress: 0,
        memory_entries: 15,
        queue_size: 0,
        connected_since: new Date(Date.now() - 1800000).toISOString(),
        last_activity: new Date(Date.now() - 120000).toISOString(),
        current_tool: null,
        scan_id: 1
      }
    ]
    setAgents(mockAgents)
    setSelectedAgent(mockAgents[0])
  }, [])

  // WebSocket connection
  useEffect(() => {
    // Connect to global agents WebSocket
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/agents/ws/global`)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'connected':
          // Initial agents list
          if (data.active_agents) {
            setAgents(data.active_agents)
          }
          break
        case 'state_change':
          setAgents(prev => prev.map(a => 
            a.id === data.agent_id 
              ? { ...a, state: data.new_state, last_activity: new Date().toISOString() }
              : a
          ))
          break
        case 'thought':
          if (data.agent_id === selectedAgent?.id) {
            setThoughts(prev => [...prev, data.thought])
          }
          break
        case 'action':
          if (data.agent_id === selectedAgent?.id) {
            setActions(prev => [...prev, data.action])
          }
          break
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
    }

    return () => ws.close()
  }, [selectedAgent?.id])

  // Fetch agent-specific data when selection changes
  useEffect(() => {
    if (!selectedAgent) return

    // Fetch thoughts and actions for selected agent
    const fetchAgentData = async () => {
      try {
        // Mock data for demonstration
        const mockThoughts: AgentThought[] = [
          {
            id: 't1',
            agent_id: selectedAgent.id,
            timestamp: new Date(Date.now() - 60000).toISOString(),
            thought_type: 'observation',
            content: 'Target has 3 open ports: 80, 443, 8080. Port 8080 appears to be running a Tomcat server.',
            confidence: 0.95,
            related_tool: 'nmap',
            metadata: {}
          },
          {
            id: 't2',
            agent_id: selectedAgent.id,
            timestamp: new Date(Date.now() - 45000).toISOString(),
            thought_type: 'reasoning',
            content: 'Tomcat on port 8080 could have default credentials or exposed manager interface. This is a high-value target for further investigation.',
            confidence: 0.82,
            related_tool: null,
            metadata: {}
          },
          {
            id: 't3',
            agent_id: selectedAgent.id,
            timestamp: new Date(Date.now() - 30000).toISOString(),
            thought_type: 'action',
            content: 'Launching Hydra brute-force attack against Tomcat manager with common credentials list.',
            confidence: 0.9,
            related_tool: 'hydra',
            metadata: { target: 'http://target:8080/manager/html' }
          },
          {
            id: 't4',
            agent_id: selectedAgent.id,
            timestamp: new Date(Date.now() - 15000).toISOString(),
            thought_type: 'observation',
            content: 'Successfully authenticated with tomcat:s3cr3t. Manager interface is accessible.',
            confidence: 1.0,
            related_tool: 'hydra',
            metadata: { credentials: 'tomcat:s3cr3t' }
          }
        ]
        setThoughts(mockThoughts)

        const mockActions: AgentAction[] = [
          {
            id: 'a1',
            agent_id: selectedAgent.id,
            timestamp: new Date(Date.now() - 120000).toISOString(),
            action_type: 'TOOL_CALL',
            target: 'target.example.com',
            parameters: { ports: '80,443,8080', scan_type: 'syn' },
            result: '3 ports open',
            duration_ms: 5234,
            success: true
          },
          {
            id: 'a2',
            agent_id: selectedAgent.id,
            timestamp: new Date(Date.now() - 45000).toISOString(),
            action_type: 'TOOL_CALL',
            target: 'http://target:8080/manager/html',
            parameters: { tool: 'hydra', wordlist: 'tomcat-betterpass.txt' },
            result: 'Credentials found: tomcat:s3cr3t',
            duration_ms: 28912,
            success: true
          }
        ]
        setActions(mockActions)
      } catch (error) {
        console.error('Failed to fetch agent data:', error)
      }
    }

    fetchAgentData()
  }, [selectedAgent])

  const handleControlAction = async (action: 'pause' | 'resume' | 'stop') => {
    if (!selectedAgent) return
    
    try {
      // Send control command
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          action: 'control',
          agent_id: selectedAgent.id,
          command: action
        }))
      }
    } catch (error) {
      console.error('Failed to send control command:', error)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Agent Monitor</h1>
          <p className="text-slate-400 mt-1">Real-time agent activity and thought process monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border',
            wsConnected 
              ? 'bg-green-500/10 text-green-400 border-green-500/30' 
              : 'bg-red-500/10 text-red-400 border-red-500/30'
          )}>
            {wsConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            {wsConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
        {/* Agent List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-200">Active Agents ({agents.length})</h3>
          </div>
          <div className="space-y-3">
            {agents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                isSelected={selectedAgent?.id === agent.id}
                onClick={() => setSelectedAgent(agent)}
              />
            ))}
          </div>
        </div>

        {/* Agent Detail */}
        {selectedAgent && (
          <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden flex flex-col">
            {/* Detail Header */}
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    'w-12 h-12 rounded-xl flex items-center justify-center',
                    STATE_COLORS[selectedAgent.state]?.bg || STATE_COLORS.idle.bg
                  )}>
                    {(ROLE_ICONS[selectedAgent.role] || Bot)({ className: cn('w-6 h-6', STATE_COLORS[selectedAgent.state]?.text || STATE_COLORS.idle.text) })}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-100">{selectedAgent.name}</h2>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-sm text-slate-400 capitalize">{selectedAgent.role.replace('_', ' ')}</span>
                      <span className="text-slate-600">•</span>
                      <span className={cn(
                        'text-sm font-medium',
                        STATE_COLORS[selectedAgent.state]?.text || STATE_COLORS.idle.text
                      )}>
                        {selectedAgent.state}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {selectedAgent.state === 'running' || selectedAgent.state === 'thinking' || selectedAgent.state === 'executing' ? (
                    <>
                      <button
                        onClick={() => handleControlAction('pause')}
                        className="p-2 hover:bg-yellow-500/10 rounded-lg text-slate-400 hover:text-yellow-400 transition-colors"
                        title="Pause Agent"
                      >
                        <Pause className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleControlAction('stop')}
                        className="p-2 hover:bg-red-500/10 rounded-lg text-slate-400 hover:text-red-400 transition-colors"
                        title="Stop Agent"
                      >
                        <Square className="w-5 h-5" />
                      </button>
                    </>
                  ) : selectedAgent.state === 'waiting' ? (
                    <button
                      onClick={() => handleControlAction('resume')}
                      className="p-2 hover:bg-green-500/10 rounded-lg text-slate-400 hover:text-green-400 transition-colors"
                      title="Resume Agent"
                    >
                      <Play className="w-5 h-5" />
                    </button>
                  ) : null}
                </div>
              </div>

              {selectedAgent.current_task && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-slate-400">Current Task</span>
                    <span className="text-slate-300">{selectedAgent.task_progress}%</span>
                  </div>
                  <p className="text-slate-200 mb-2">{selectedAgent.current_task}</p>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                      style={{ width: `${selectedAgent.task_progress}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-4 gap-4 mt-6">
                <div className="bg-slate-700/30 rounded-lg p-3">
                  <div className="text-2xl font-bold text-slate-200">{selectedAgent.memory_entries}</div>
                  <div className="text-xs text-slate-500">Memory Entries</div>
                </div>
                <div className="bg-slate-700/30 rounded-lg p-3">
                  <div className="text-2xl font-bold text-slate-200">{selectedAgent.queue_size}</div>
                  <div className="text-xs text-slate-500">Queue Size</div>
                </div>
                <div className="bg-slate-700/30 rounded-lg p-3">
                  <div className="text-2xl font-bold text-slate-200">
                    {formatDistanceToNow(new Date(selectedAgent.connected_since), { addSuffix: false })}
                  </div>
                  <div className="text-xs text-slate-500">Connected For</div>
                </div>
                <div className="bg-slate-700/30 rounded-lg p-3">
                  <div className="text-2xl font-bold text-slate-200 truncate">{selectedAgent.current_tool || 'None'}</div>
                  <div className="text-xs text-slate-500">Current Tool</div>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-700">
              <button
                onClick={() => setActiveTab('thoughts')}
                className={cn(
                  'flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                  activeTab === 'thoughts'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                )}
              >
                <Brain className="w-4 h-4 inline mr-2" />
                Thought Process
              </button>
              <button
                onClick={() => setActiveTab('actions')}
                className={cn(
                  'flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                  activeTab === 'actions'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                )}
              >
                <Terminal className="w-4 h-4 inline mr-2" />
                Action Log
              </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'thoughts' ? (
              <ThoughtStream thoughts={thoughts} agentId={selectedAgent.id} />
            ) : (
              <ActionLog actions={actions} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
