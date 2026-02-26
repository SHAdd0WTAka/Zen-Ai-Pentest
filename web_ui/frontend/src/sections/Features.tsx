import { useEffect, useRef, useState } from 'react';
import {
  Brain,
  Shield,
  Zap,
  Server,
  FileText,
  Container,
  Workflow,
  Cloud,
  QrCode,
} from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'Autonomous AI Agent',
    description:
      'ReAct pattern implementation with state machine: IDLE → PLANNING → EXECUTING → OBSERVING → REFLECTING → COMPLETED',
    color: 'from-purple-500 to-pink-500',
    highlights: ['Reason → Act → Observe → Reflect', 'Multi-agent cooperation', 'Intelligent decision making'],
  },
  {
    icon: Shield,
    title: 'Safety First',
    description:
      'Multiple layers of safety controls to protect your infrastructure during testing',
    color: 'from-green-500 to-emerald-500',
    highlights: ['Private IP blocking', 'Timeout management', 'Resource limits', 'Read-only filesystems'],
  },
  {
    icon: Zap,
    title: '72+ Security Tools',
    description:
      'Real execution of professional security tools with no simulations or mocks',
    color: 'from-yellow-500 to-orange-500',
    highlights: ['Nmap, Nuclei, SQLMap', 'FFuF, WhatWeb, Nikto', 'Subfinder, HTTPX', 'WAFW00F'],
  },
  {
    icon: Server,
    title: 'Modern API & Backend',
    description:
      'High-performance REST API built with FastAPI and PostgreSQL for persistent storage',
    color: 'from-cyan-500 to-blue-500',
    highlights: ['FastAPI framework', 'PostgreSQL database', 'WebSocket support', 'JWT Auth with RBAC'],
  },
  {
    icon: FileText,
    title: 'Comprehensive Reporting',
    description:
      'Generate professional reports in multiple formats for different audiences',
    color: 'from-indigo-500 to-violet-500',
    highlights: ['PDF reports', 'HTML Dashboard', 'JSON/XML export', 'Slack/Email alerts'],
  },
  {
    icon: Container,
    title: 'Docker Sandbox',
    description:
      'Isolated tool execution environment for maximum safety and reproducibility',
    color: 'from-blue-500 to-cyan-500',
    highlights: ['Containerized execution', 'Guest VM control', 'Resource isolation', 'Easy deployment'],
  },
  {
    icon: Workflow,
    title: 'CI/CD Integration',
    description:
      'Production-ready with GitHub Actions pipeline and enterprise deployment options',
    color: 'from-red-500 to-rose-500',
    highlights: ['GitHub Actions', 'GitLab CI', 'Jenkins support', 'Kubernetes ready'],
  },
  {
    icon: Cloud,
    title: 'Cloud-Native',
    description:
      'Deploy on major cloud providers with Docker Compose or Kubernetes',
    color: 'from-sky-500 to-blue-500',
    highlights: ['AWS ready', 'Azure support', 'GCP compatible', 'Auto-scaling'],
  },
  {
    icon: QrCode,
    title: 'Quick Access',
    description:
      'Scan QR codes for instant mobile access to scan results and dashboards',
    color: 'from-teal-500 to-green-500',
    highlights: ['Mobile-friendly', 'QR code generation', 'Instant access', 'Responsive design'],
  },
];

export function Features() {
  const [visibleCards, setVisibleCards] = useState<Set<number>>(new Set());
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const observers: IntersectionObserver[] = [];

    cardRefs.current.forEach((ref, index) => {
      if (!ref) return;

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setVisibleCards((prev) => new Set([...prev, index]));
          }
        },
        { threshold: 0.2 }
      );

      observer.observe(ref);
      observers.push(observer);
    });

    return () => {
      observers.forEach((observer) => observer.disconnect());
    };
  }, []);

  return (
    <section id="features" className="relative py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-[128px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            <span>Powerful Features</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            Everything You Need for
            <br />
            <span className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
              Professional Penetration Testing
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Zen-AI-Pentest provides a complete suite of tools and features for
            autonomous security assessments with enterprise-grade reliability.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              ref={(el) => { cardRefs.current[index] = el; }}
              className={`group relative p-6 rounded-2xl bg-slate-900/50 border border-slate-800/50 hover:border-slate-700/50 transition-all duration-500 hover:scale-[1.02] ${
                visibleCards.has(index)
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-8'
              }`}
              style={{ transitionDelay: `${index * 50}ms` }}
            >
              {/* Glow Effect */}
              <div
                className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity duration-500`}
              />

              {/* Icon */}
              <div
                className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.color} mb-5 shadow-lg`}
              >
                <feature.icon className="w-6 h-6 text-white" />
              </div>

              {/* Title */}
              <h3 className="text-xl font-bold text-white mb-3 group-hover:text-cyan-400 transition-colors">
                {feature.title}
              </h3>

              {/* Description */}
              <p className="text-slate-400 mb-4 text-sm leading-relaxed">
                {feature.description}
              </p>

              {/* Highlights */}
              <ul className="space-y-2">
                {feature.highlights.map((highlight, hIndex) => (
                  <li
                    key={hIndex}
                    className="flex items-center gap-2 text-sm text-slate-500"
                  >
                    <div className={`w-1.5 h-1.5 rounded-full bg-gradient-to-r ${feature.color}`} />
                    {highlight}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
