import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Shield,
  Terminal,
  Zap,
  Lock,
  ChevronRight,
  Play,
  Sparkles,
} from 'lucide-react';

export function Hero() {
  const [isVisible, setIsVisible] = useState(false);
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const scrollToSection = (href: string) => {
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section
      ref={heroRef}
      className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden"
    >
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Gradient Orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-[128px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[128px] animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-[150px]" />

        {/* Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
              linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)`,
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div
            className={`space-y-8 transition-all duration-1000 ${
              isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-12'
            }`}
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              <span>AI-Powered Penetration Testing</span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">
              <span className="text-white">Autonomous Security</span>
              <br />
              <span className="bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                Testing Framework
              </span>
            </h1>

            {/* Description */}
            <p className="text-lg text-slate-400 max-w-xl leading-relaxed">
              Zen-AI-Pentest combines cutting-edge AI with 40+ professional security
              tools. Execute real vulnerability scans with intelligent automation,
              comprehensive reporting, and enterprise-grade safety controls.
            </p>

            {/* Key Features Pills */}
            <div className="flex flex-wrap gap-3">
              {[
                { icon: Shield, text: '40+ Security Tools' },
                { icon: Terminal, text: 'Real Execution' },
                { icon: Zap, text: 'AI-Powered' },
                { icon: Lock, text: 'Safety First' },
              ].map((feature, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-300 text-sm"
                >
                  <feature.icon className="w-4 h-4 text-cyan-400" />
                  {feature.text}
                </div>
              ))}
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4">
              <Button
                size="lg"
                className="bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white border-0 text-lg px-8"
                onClick={() => scrollToSection('#getting-started')}
              >
                Get Started
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-slate-600 text-slate-300 hover:bg-slate-800/50 hover:text-white text-lg px-8"
                onClick={() => scrollToSection('#features')}
              >
                <Play className="w-5 h-5 mr-2" />
                Explore Features
              </Button>
            </div>

            {/* Stats Row */}
            <div className="flex gap-8 pt-4">
              {[
                { value: '205+', label: 'GitHub Stars' },
                { value: '40+', label: 'Security Tools' },
                { value: 'v2.3.9', label: 'Latest Version' },
              ].map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-sm text-slate-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Content - Terminal Demo */}
          <div
            className={`relative transition-all duration-1000 delay-300 ${
              isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-12'
            }`}
          >
            <div className="relative">
              {/* Glow Effect */}
              <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-2xl blur-xl" />

              {/* Terminal Window */}
              <div className="relative bg-slate-900 rounded-xl border border-slate-700/50 overflow-hidden shadow-2xl">
                {/* Terminal Header */}
                <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 border-b border-slate-700/50">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <div className="ml-4 text-sm text-slate-500 font-mono">
                    zen-ai-pentest --target example.com
                  </div>
                </div>

                {/* Terminal Content */}
                <div className="p-6 font-mono text-sm space-y-2">
                  <div className="text-green-400">
                    $ zen-ai-pentest --target example.com --mode autonomous
                  </div>
                  <div className="text-slate-400">
                    [INFO] Initializing Zen-AI-Pentest v2.3.9...
                  </div>
                  <div className="text-slate-400">
                    [INFO] Loading AI agents (Researcher, Analyst)...
                  </div>
                  <div className="text-cyan-400">
                    [AI] Analyzing target scope and planning attack vectors...
                  </div>
                  <div className="text-slate-400">
                    [TOOL] Executing: nmap -sV -sC example.com
                  </div>
                  <div className="text-green-400">
                    [RESULT] Open ports: 80 (HTTP), 443 (HTTPS), 22 (SSH)
                  </div>
                  <div className="text-slate-400">
                    [TOOL] Executing: nuclei -u example.com
                  </div>
                  <div className="text-yellow-400">
                    [FINDING] CVE-2023-XXXX: Medium severity vulnerability detected
                  </div>
                  <div className="text-cyan-400">
                    [AI] Recommending: Further investigation on /api endpoint
                  </div>
                  <div className="text-slate-400">
                    [TOOL] Executing: ffuf -u example.com/FUZZ
                  </div>
                  <div className="text-green-400">
                    [RESULT] Discovered: /admin, /api/v1, /docs
                  </div>
                  <div className="text-purple-400 animate-pulse">
                    [AI] Generating comprehensive report...
                  </div>
                  <div className="flex items-center gap-2 text-cyan-400">
                    <span className="animate-pulse">_</span>
                  </div>
                </div>
              </div>

              {/* Floating Badges */}
              <div className="absolute -top-4 -right-4 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg shadow-lg animate-bounce">
                <span className="text-white font-semibold text-sm">AI Powered</span>
              </div>
              <div
                className="absolute -bottom-4 -left-4 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg shadow-lg animate-bounce"
                style={{ animationDelay: '0.5s' }}
              >
                <span className="text-white font-semibold text-sm">Real Tools</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 rounded-full border-2 border-slate-600 flex justify-center pt-2">
          <div className="w-1.5 h-3 bg-slate-400 rounded-full animate-pulse" />
        </div>
      </div>
    </section>
  );
}
