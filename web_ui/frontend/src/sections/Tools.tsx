import { useState, useEffect, useRef } from 'react';
import {
  Search,
  Globe,
  Database,
  Lock,
  Terminal,
  Shield,
  Zap,
  Code,
  Server,
  Fingerprint,
  Eye,
  Bug,
  Network,
  FileSearch,
  Radio,
  Wifi,
  Layers,
  Cpu,
  Cloud,
} from 'lucide-react';

const toolCategories = [
  {
    name: 'Network Scanning',
    icon: Network,
    color: 'from-cyan-500 to-blue-500',
    tools: [
      { name: 'Nmap', description: 'Port scanning with XML output parsing', icon: Search },
      { name: 'Masscan', description: 'Internet-scale port scanner', icon: Zap },
      { name: 'Naabu', description: 'Fast port scanner written in Go', icon: Server },
    ],
  },
  {
    name: 'Web Scanning',
    icon: Globe,
    color: 'from-purple-500 to-pink-500',
    tools: [
      { name: 'Nuclei', description: 'Vulnerability detection with JSON output', icon: Bug },
      { name: 'Nikto', description: 'Web vulnerability scanner', icon: Shield },
      { name: 'OWASP ZAP', description: 'Web application security scanner', icon: Lock },
    ],
  },
  {
    name: 'Fuzzing',
    icon: Terminal,
    color: 'from-yellow-500 to-orange-500',
    tools: [
      { name: 'FFuF', description: 'Blazing fast web fuzzer', icon: Zap },
      { name: 'Gobuster', description: 'Directory/file & DNS busting', icon: FileSearch },
      { name: 'Wfuzz', description: 'Web application fuzzer', icon: Code },
    ],
  },
  {
    name: 'Subdomain Discovery',
    icon: Layers,
    color: 'from-green-500 to-emerald-500',
    tools: [
      { name: 'Subfinder', description: 'Subdomain enumeration', icon: Search },
      { name: 'Amass', description: 'In-depth attack surface mapping', icon: Network },
      { name: 'Assetfinder', description: 'Find domains and subdomains', icon: Globe },
    ],
  },
  {
    name: 'HTTP Probing',
    icon: Wifi,
    color: 'from-indigo-500 to-violet-500',
    tools: [
      { name: 'HTTPX', description: 'Fast HTTP prober', icon: Zap },
      { name: 'Httprobe', description: 'Take a list of domains and probe for working HTTP/HTTPS', icon: Server },
    ],
  },
  {
    name: 'Technology Detection',
    icon: Cpu,
    color: 'from-red-500 to-rose-500',
    tools: [
      { name: 'WhatWeb', description: 'Technology detection (900+ plugins)', icon: Fingerprint },
      { name: 'Wappalyzer', description: 'Identifies technologies on websites', icon: Eye },
      { name: 'WAFW00F', description: 'WAF detection (50+ signatures)', icon: Shield },
    ],
  },
  {
    name: 'SQL Injection',
    icon: Database,
    color: 'from-teal-500 to-cyan-500',
    tools: [
      { name: 'SQLMap', description: 'SQL injection testing with safety controls', icon: Bug },
    ],
  },
  {
    name: 'Secret Scanning',
    icon: Lock,
    color: 'from-pink-500 to-rose-500',
    tools: [
      { name: 'TruffleHog', description: 'Find credentials in code', icon: Eye },
      { name: 'GitLeaks', description: 'Detect hardcoded secrets', icon: Shield },
    ],
  },
  {
    name: 'Cloud Security',
    icon: Cloud,
    color: 'from-sky-500 to-blue-500',
    tools: [
      { name: 'ScoutSuite', description: 'Multi-cloud security auditing', icon: Shield },
      { name: 'Prowler', description: 'AWS security best practices', icon: Lock },
      { name: 'Trivy', description: 'Container image vulnerability scanner', icon: Bug },
    ],
  },
  {
    name: 'Static Analysis',
    icon: Code,
    color: 'from-orange-500 to-amber-500',
    tools: [
      { name: 'Semgrep', description: 'Static analysis for code security', icon: Search },
      { name: 'Bandit', description: 'Python security linter', icon: Shield },
    ],
  },
  {
    name: 'Wireless',
    icon: Radio,
    color: 'from-lime-500 to-green-500',
    tools: [
      { name: 'Aircrack-ng', description: 'WiFi security auditing', icon: Wifi },
    ],
  },
  {
    name: 'Exploitation',
    icon: Zap,
    color: 'from-red-600 to-red-500',
    tools: [
      { name: 'Metasploit', description: 'Penetration testing framework', icon: Bug },
    ],
  },
];

export function Tools() {
  const [activeCategory, setActiveCategory] = useState(0);
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
      id="tools"
      ref={sectionRef}
      className="relative py-24 overflow-hidden"
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900/30 to-slate-950" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div
          className={`text-center mb-16 transition-all duration-700 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium mb-6">
            <Terminal className="w-4 h-4" />
            <span>Integrated Tools</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            72+ Professional
            <br />
            <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
              Security Tools
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Real execution of industry-standard security tools with intelligent
            orchestration and comprehensive result aggregation.
          </p>
        </div>

        {/* Category Tabs */}
        <div
          className={`flex flex-wrap justify-center gap-2 mb-10 transition-all duration-700 delay-100 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {toolCategories.map((category, index) => (
            <button
              key={index}
              onClick={() => setActiveCategory(index)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                activeCategory === index
                  ? 'bg-slate-800 text-white border border-slate-700'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <category.icon className="w-4 h-4" />
              {category.name}
            </button>
          ))}
        </div>

        {/* Tools Grid */}
        <div
          className={`transition-all duration-700 delay-200 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {toolCategories[activeCategory].tools.map((tool, index) => (
              <div
                key={index}
                className="group relative p-5 rounded-xl bg-slate-900/50 border border-slate-800/50 hover:border-slate-700/50 transition-all duration-300 hover:scale-[1.02]"
              >
                {/* Glow */}
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${toolCategories[activeCategory].color} opacity-0 group-hover:opacity-5 rounded-xl transition-opacity`}
                />

                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className={`flex-shrink-0 p-2.5 rounded-lg bg-gradient-to-br ${toolCategories[activeCategory].color}`}
                  >
                    <tool.icon className="w-5 h-5 text-white" />
                  </div>

                  {/* Content */}
                  <div>
                    <h4 className="font-semibold text-white mb-1 group-hover:text-cyan-400 transition-colors">
                      {tool.name}
                    </h4>
                    <p className="text-sm text-slate-400">{tool.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Category Info */}
          <div className="mt-8 p-4 rounded-lg bg-slate-900/30 border border-slate-800/50 text-center">
            <p className="text-slate-500 text-sm">
              Showing {toolCategories[activeCategory].tools.length} tools in{' '}
              <span className="text-cyan-400 font-medium">
                {toolCategories[activeCategory].name}
              </span>{' '}
              category
            </p>
          </div>
        </div>

        {/* All Tools Summary */}
        <div
          className={`mt-16 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 transition-all duration-700 delay-300 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {toolCategories.map((category, index) => (
            <div
              key={index}
              className="p-4 rounded-lg bg-slate-900/30 border border-slate-800/30 text-center"
            >
              <div
                className={`inline-flex p-2 rounded-lg bg-gradient-to-br ${category.color} mb-2`}
              >
                <category.icon className="w-4 h-4 text-white" />
              </div>
              <div className="text-lg font-bold text-white">{category.tools.length}</div>
              <div className="text-xs text-slate-500">{category.name}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
