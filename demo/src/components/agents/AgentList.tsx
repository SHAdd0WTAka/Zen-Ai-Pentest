import { useState } from 'react';
import { Users, Activity, Cpu, HardDrive } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: string;
  cpu: number;
  memory: number;
  tasks: number;
  capabilities: string[];
  ip: string;
}

export function AgentList({ agents }: { agents: Agent[] }) {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Users className="w-5 h-5 text-cyan-500" />
          Agents ({agents.length})
        </h2>
      </div>

      <div className="grid gap-3">
        {agents.map((agent) => (
          <div
            key={agent.id}
            onClick={() => setSelectedAgent(agent)}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              selectedAgent?.id === agent.id
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-slate-200">{agent.name}</h3>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs ${
                      agent.status === 'online'
                        ? 'bg-green-500/20 text-green-400'
                        : agent.status === 'busy'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>
                <p className="text-sm text-slate-500 mt-1">{agent.ip}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-cyan-400">{agent.tasks}</p>
                <p className="text-xs text-slate-500">tasks</p>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-4">
              <div className="flex items-center gap-1.5 text-sm">
                <Cpu className="w-4 h-4 text-slate-500" />
                <span className={agent.cpu > 80 ? 'text-red-400' : 'text-slate-400'}>
                  {agent.cpu}%
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-sm">
                <HardDrive className="w-4 h-4 text-slate-500" />
                <span className={agent.memory > 80 ? 'text-red-400' : 'text-slate-400'}>
                  {agent.memory}%
                </span>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap gap-1">
              {agent.capabilities.map((cap) => (
                <span
                  key={cap}
                  className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-400"
                >
                  {cap}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
