import { useState, useEffect, useRef } from 'react';
import {
  Terminal,
  Copy,
  Check,
  Download,
  Container,
  Github,
  Rocket,
  Shield,
  Zap,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const installMethods = [
  {
    name: 'Docker',
    icon: Container,
    color: 'from-blue-500 to-cyan-500',
    description: 'Recommended for production deployment',
    steps: [
      {
        title: 'Clone the repository',
        command: 'git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git',
      },
      {
        title: 'Navigate to project directory',
        command: 'cd Zen-Ai-Pentest',
      },
      {
        title: 'Start with Docker Compose',
        command: 'docker-compose up -d',
      },
      {
        title: 'Access the application',
        command: 'Open http://localhost:3000 in your browser',
      },
    ],
  },
  {
    name: 'Python',
    icon: Terminal,
    color: 'from-yellow-500 to-orange-500',
    description: 'For development and local testing',
    steps: [
      {
        title: 'Clone the repository',
        command: 'git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git',
      },
      {
        title: 'Create virtual environment',
        command: 'python -m venv venv && source venv/bin/activate',
      },
      {
        title: 'Install dependencies',
        command: 'pip install -r requirements.txt',
      },
      {
        title: 'Run the application',
        command: 'python zen_ai_pentest.py',
      },
    ],
  },
  {
    name: 'GitHub Action',
    icon: Github,
    color: 'from-slate-500 to-slate-700',
    description: 'Integrate into your CI/CD pipeline',
    steps: [
      {
        title: 'Add to your workflow',
        command: `- name: Run Zen-AI-Pentest
  uses: SHAdd0WTAka/Zen-Ai-Pentest@v2.3.9
  with:
    target: 'https://your-app.com'
    mode: 'autonomous'`,
      },
      {
        title: 'Configure secrets',
        command: 'Add ZEN_API_KEY to repository secrets',
      },
    ],
  },
];

const quickStartSteps = [
  {
    number: '01',
    title: 'Install',
    description: 'Choose your preferred installation method above',
    icon: Download,
  },
  {
    number: '02',
    title: 'Configure',
    description: 'Set up your API keys and environment variables',
    icon: Shield,
  },
  {
    number: '03',
    title: 'Launch',
    description: 'Start the application and access the dashboard',
    icon: Rocket,
  },
  {
    number: '04',
    title: 'Scan',
    description: 'Run your first autonomous penetration test',
    icon: Zap,
  },
];

export function GettingStarted() {
  const [isVisible, setIsVisible] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);
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

  const copyToClipboard = (text: string, index: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section
      id="getting-started"
      ref={sectionRef}
      className="relative py-24 overflow-hidden"
    >
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-green-500/5 rounded-full blur-[128px]" />
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-[128px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div
          className={`text-center mb-16 transition-all duration-700 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium mb-6">
            <Rocket className="w-4 h-4" />
            <span>Getting Started</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            Start Testing in
            <br />
            <span className="bg-gradient-to-r from-green-400 to-cyan-500 bg-clip-text text-transparent">
              Minutes, Not Hours
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Get up and running quickly with our easy installation options.
            Choose the method that works best for your environment.
          </p>
        </div>

        {/* Quick Start Steps */}
        <div
          className={`grid grid-cols-2 md:grid-cols-4 gap-6 mb-16 transition-all duration-700 delay-100 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {quickStartSteps.map((step, index) => (
            <div
              key={index}
              className="relative p-6 rounded-xl bg-slate-900/50 border border-slate-800/50 hover:border-slate-700/50 transition-all duration-300 group"
            >
              {/* Step Number */}
              <div className="absolute -top-3 -left-2 w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-cyan-500 flex items-center justify-center text-white font-bold text-sm">
                {step.number}
              </div>

              {/* Icon */}
              <div className="mb-4">
                <step.icon className="w-8 h-8 text-slate-400 group-hover:text-cyan-400 transition-colors" />
              </div>

              {/* Content */}
              <h4 className="font-semibold text-white mb-2">{step.title}</h4>
              <p className="text-sm text-slate-400">{step.description}</p>

              {/* Connector Line (hidden on last item and mobile) */}
              {index < quickStartSteps.length - 1 && (
                <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-0.5 bg-slate-800">
                  <ChevronRight className="absolute right-0 -top-2 w-4 h-4 text-slate-600" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Installation Tabs */}
        <div
          className={`transition-all duration-700 delay-200 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <Tabs defaultValue="Docker" className="w-full">
            <TabsList className="grid w-full max-w-lg mx-auto grid-cols-3 mb-8 bg-slate-900/50 border border-slate-800/50">
              {installMethods.map((method) => (
                <TabsTrigger
                  key={method.name}
                  value={method.name}
                  className="data-[state=active]:bg-slate-800 data-[state=active]:text-white"
                >
                  <method.icon className="w-4 h-4 mr-2" />
                  {method.name}
                </TabsTrigger>
              ))}
            </TabsList>

            {installMethods.map((method) => (
              <TabsContent key={method.name} value={method.name}>
                <div className="rounded-xl bg-slate-900/50 border border-slate-800/50 overflow-hidden">
                  {/* Method Header */}
                  <div className="p-6 border-b border-slate-800/50">
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className={`p-2 rounded-lg bg-gradient-to-br ${method.color}`}
                      >
                        <method.icon className="w-5 h-5 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-white">
                        Install with {method.name}
                      </h3>
                    </div>
                    <p className="text-slate-400">{method.description}</p>
                  </div>

                  {/* Steps */}
                  <div className="p-6 space-y-4">
                    {method.steps.map((step, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-xs text-slate-400">
                            {index + 1}
                          </span>
                          <span className="text-sm text-slate-300">
                            {step.title}
                          </span>
                        </div>
                        <div className="relative">
                          <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800/50 text-sm text-slate-300 overflow-x-auto font-mono">
                            <code>{step.command}</code>
                          </pre>
                          <button
                            onClick={() =>
                              copyToClipboard(
                                step.command,
                                `${method.name}-${index}`
                              )
                            }
                            className="absolute top-2 right-2 p-2 rounded-lg bg-slate-800/50 text-slate-400 hover:text-white transition-colors"
                          >
                            {copiedIndex === `${method.name}-${index}` ? (
                              <Check className="w-4 h-4 text-green-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </div>

        {/* CTA Buttons */}
        <div
          className={`mt-12 flex flex-wrap justify-center gap-4 transition-all duration-700 delay-300 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <a
            href="https://github.com/SHAdd0WTAka/Zen-Ai-Pentest"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button
              size="lg"
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-800/50 hover:text-white"
            >
              <Github className="w-5 h-5 mr-2" />
              View on GitHub
            </Button>
          </a>
          <a
            href="https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/QUICKSTART.md"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button
              size="lg"
              className="bg-gradient-to-r from-green-500 to-cyan-500 hover:from-green-400 hover:to-cyan-400 text-white border-0"
            >
              <Terminal className="w-5 h-5 mr-2" />
              Read Quickstart Guide
            </Button>
          </a>
        </div>

        {/* Requirements */}
        <div
          className={`mt-12 p-6 rounded-xl bg-slate-900/30 border border-slate-800/50 transition-all duration-700 delay-400 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <h4 className="font-semibold text-white mb-4">System Requirements</h4>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { label: 'Python', value: '3.9 or higher' },
              { label: 'Docker', value: '20.10 or higher' },
              { label: 'Memory', value: '4GB RAM minimum' },
              { label: 'Storage', value: '10GB free space' },
              { label: 'Network', value: 'Internet access' },
              { label: 'OS', value: 'Linux/macOS/Windows' },
            ].map((req, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50"
              >
                <span className="text-sm text-slate-400">{req.label}</span>
                <span className="text-sm text-cyan-400">{req.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
