import { useEffect, useRef, useState } from 'react';
import {
  Server,
  Database,
  Cpu,
  Shield,
  Lock,
  Zap,
  Globe,
  Container,
  Workflow,
  Bell,
  FileText,
  Users,
  Layers,
  Code,
} from 'lucide-react';

const architectureLayers = [
  {
    name: 'Frontend Layer',
    icon: Globe,
    color: 'from-cyan-500 to-blue-500',
    items: [
      { name: 'React + TypeScript', icon: Code, desc: 'Modern UI framework' },
      { name: 'Tailwind CSS', icon: Layers, desc: 'Utility-first styling' },
      { name: 'WebSocket Client', icon: Zap, desc: 'Real-time updates' },
      { name: 'Responsive Design', icon: Globe, desc: 'Mobile & desktop' },
    ],
  },
  {
    name: 'API Layer',
    icon: Server,
    color: 'from-purple-500 to-pink-500',
    items: [
      { name: 'FastAPI', icon: Zap, desc: 'High-performance REST API' },
      { name: 'WebSocket', icon: Zap, desc: 'Real-time communication' },
      { name: 'JWT Auth', icon: Lock, desc: 'Role-based access control' },
      { name: 'Background Tasks', icon: Workflow, desc: 'Async execution' },
    ],
  },
  {
    name: 'AI Agent Layer',
    icon: Cpu,
    color: 'from-yellow-500 to-orange-500',
    items: [
      { name: 'ReAct Pattern', icon: Zap, desc: 'Reason-Act-Observe-Reflect' },
      { name: 'Multi-Agent', icon: Users, desc: 'Researcher & Analyst' },
      { name: 'State Machine', icon: Workflow, desc: 'Managed execution flow' },
      { name: 'LLM Integration', icon: Cpu, desc: 'OpenAI/Anthropic/Ollama' },
    ],
  },
  {
    name: 'Tool Execution Layer',
    icon: Shield,
    color: 'from-green-500 to-emerald-500',
    items: [
      { name: 'Docker Sandbox', icon: Container, desc: 'Isolated execution' },
      { name: '72+ Tools', icon: Shield, desc: 'Security tool suite' },
      { name: 'Safety Controls', icon: Lock, desc: 'IP blocking, timeouts' },
      { name: 'Result Parser', icon: FileText, desc: 'Output processing' },
    ],
  },
  {
    name: 'Data Layer',
    icon: Database,
    color: 'from-indigo-500 to-violet-500',
    items: [
      { name: 'PostgreSQL', icon: Database, desc: 'Persistent storage' },
      { name: 'Alembic', icon: Code, desc: 'Database migrations' },
      { name: 'Redis', icon: Zap, desc: 'Caching & queues' },
      { name: 'File Storage', icon: FileText, desc: 'Reports & evidence' },
    ],
  },
  {
    name: 'Infrastructure Layer',
    icon: Server,
    color: 'from-red-500 to-rose-500',
    items: [
      { name: 'Docker Compose', icon: Container, desc: 'Container orchestration' },
      { name: 'Nginx', icon: Globe, desc: 'Reverse proxy' },
      { name: 'CI/CD', icon: Workflow, desc: 'GitHub Actions' },
      { name: 'Monitoring', icon: Bell, desc: 'Health checks & alerts' },
    ],
  },
];

export function Architecture() {
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section
      id="architecture"
      ref={sectionRef}
      className="relative py-24 overflow-hidden"
    >
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-cyan-500/5 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div
          className={`text-center mb-16 transition-all duration-700 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium mb-6">
            <Layers className="w-4 h-4" />
            <span>System Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            Enterprise-Grade
            <br />
            <span className="bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent">
              Technical Architecture
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Built with modern technologies for scalability, security, and performance.
            Deploy anywhere with Docker or Kubernetes.
          </p>
        </div>

        {/* Architecture Diagram */}
        <div
          className={`relative mb-16 transition-all duration-700 delay-100 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {/* Connection Lines */}
          <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500/50 via-purple-500/50 to-indigo-500/50" />

          {/* Layers */}
          <div className="space-y-8">
            {architectureLayers.map((layer, index) => (
              <div
                key={index}
                className={`relative transition-all duration-500`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                {/* Layer Card */}
                <div className="lg:grid lg:grid-cols-12 lg:gap-8 items-center">
                  {/* Left Side (alternating) */}
                  <div
                    className={`hidden lg:block ${
                      index % 2 === 0 ? 'col-span-5 order-1' : 'col-span-5 order-2'
                    }`}
                  >
                    <div
                      className={`p-6 rounded-xl bg-slate-900/50 border border-slate-800/50 hover:border-slate-700/50 transition-all duration-300 group ${
                        index % 2 === 0 ? 'text-right' : 'text-left'
                      }`}
                    >
                      <div
                        className={`inline-flex items-center gap-3 mb-4 ${
                          index % 2 === 0 ? 'flex-row-reverse' : ''
                        }`}
                      >
                        <div
                          className={`p-2 rounded-lg bg-gradient-to-br ${layer.color}`}
                        >
                          <layer.icon className="w-5 h-5 text-white" />
                        </div>
                        <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">
                          {layer.name}
                        </h3>
                      </div>
                      <div
                        className={`space-y-2 ${index % 2 === 0 ? 'text-right' : 'text-left'}`}
                      >
                        {layer.items.map((item, i) => (
                          <div
                            key={i}
                            className={`inline-flex items-center gap-2 text-sm text-slate-400 ${
                              index % 2 === 0 ? 'flex-row-reverse' : ''
                            }`}
                          >
                            <span>{item.name}</span>
                            <span className="text-slate-600">•</span>
                            <span className="text-slate-500">{item.desc}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Center Node */}
                  <div className="hidden lg:flex col-span-2 order-2 justify-center">
                    <div
                      className={`w-12 h-12 rounded-full bg-gradient-to-br ${layer.color} flex items-center justify-center shadow-lg shadow-${layer.color.split('-')[1]}-500/20`}
                    >
                      <span className="text-white font-bold">{index + 1}</span>
                    </div>
                  </div>

                  {/* Right Side (alternating) */}
                  <div
                    className={`lg:hidden ${
                      index % 2 === 0 ? 'col-span-5 order-2' : 'col-span-5 order-1'
                    }`}
                  >
                    <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800/50">
                      <div className="flex items-center gap-3 mb-4">
                        <div
                          className={`p-2 rounded-lg bg-gradient-to-br ${layer.color}`}
                        >
                          <layer.icon className="w-5 h-5 text-white" />
                        </div>
                        <h3 className="text-lg font-bold text-white">{layer.name}</h3>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        {layer.items.map((item, i) => (
                          <div
                            key={i}
                            className="flex items-center gap-2 text-sm text-slate-400"
                          >
                            <item.icon className="w-4 h-4 text-slate-500" />
                            <span>{item.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Mobile View */}
                  <div className="lg:hidden">
                    <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800/50 mb-4">
                      <div className="flex items-center gap-3 mb-4">
                        <div
                          className={`p-2 rounded-lg bg-gradient-to-br ${layer.color}`}
                        >
                          <layer.icon className="w-5 h-5 text-white" />
                        </div>
                        <h3 className="text-lg font-bold text-white">{layer.name}</h3>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {layer.items.map((item, i) => (
                          <div
                            key={i}
                            className="flex items-center gap-2 text-sm text-slate-400"
                          >
                            <item.icon className="w-4 h-4 text-slate-500" />
                            <span>{item.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack Grid */}
        <div
          className={`grid grid-cols-2 md:grid-cols-4 gap-4 transition-all duration-700 delay-500 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {[
            { name: 'Python', desc: 'Backend', color: 'from-yellow-400 to-yellow-600' },
            { name: 'TypeScript', desc: 'Frontend', color: 'from-blue-400 to-blue-600' },
            { name: 'FastAPI', desc: 'API Framework', color: 'from-teal-400 to-teal-600' },
            { name: 'PostgreSQL', desc: 'Database', color: 'from-blue-500 to-indigo-600' },
            { name: 'Docker', desc: 'Containers', color: 'from-cyan-400 to-blue-500' },
            { name: 'Redis', desc: 'Caching', color: 'from-red-400 to-red-600' },
            { name: 'Nginx', desc: 'Proxy', color: 'from-green-400 to-green-600' },
            { name: 'React', desc: 'UI Library', color: 'from-cyan-400 to-blue-400' },
          ].map((tech, index) => (
            <div
              key={index}
              className="p-4 rounded-lg bg-slate-900/30 border border-slate-800/30 text-center hover:border-slate-700/50 transition-all duration-300"
            >
              <div
                className={`w-3 h-3 rounded-full bg-gradient-to-r ${tech.color} mx-auto mb-2`}
              />
              <div className="font-semibold text-white">{tech.name}</div>
              <div className="text-xs text-slate-500">{tech.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
