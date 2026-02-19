import { useState, useEffect, useRef } from 'react';
import {
  Code,
  Copy,
  Check,
  Terminal,
  Zap,
  Lock,
  Globe,
  Bell,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const apiEndpoints = [
  {
    method: 'POST',
    path: '/api/v1/scans',
    name: 'Create Scan',
    description: 'Initiate a new penetration test scan',
    auth: true,
    request: `{
  "target": "example.com",
  "mode": "autonomous",
  "tools": ["nmap", "nuclei", "ffuf"],
  "options": {
    "depth": "comprehensive",
    "timeout": 3600
  }
}`,
    response: `{
  "scan_id": "scan_abc123",
  "status": "queued",
  "target": "example.com",
  "mode": "autonomous",
  "created_at": "2026-02-19T10:30:00Z",
  "webhook_url": "https://api.example.com/webhooks/scan"
}`,
  },
  {
    method: 'GET',
    path: '/api/v1/scans/{scan_id}',
    name: 'Get Scan Status',
    description: 'Retrieve scan status and progress',
    auth: true,
    request: `// No request body required`,
    response: `{
  "scan_id": "scan_abc123",
  "status": "running",
  "progress": 65,
  "target": "example.com",
  "current_tool": "nuclei",
  "findings_count": 12,
  "started_at": "2026-02-19T10:30:00Z",
  "estimated_completion": "2026-02-19T11:15:00Z"
}`,
  },
  {
    method: 'GET',
    path: '/api/v1/scans/{scan_id}/results',
    name: 'Get Results',
    description: 'Retrieve scan findings and results',
    auth: true,
    request: `// No request body required`,
    response: `{
  "scan_id": "scan_abc123",
  "findings": [
    {
      "id": "finding_001",
      "severity": "high",
      "tool": "nuclei",
      "title": "CVE-2023-XXXX",
      "description": "Critical vulnerability detected",
      "evidence": "...",
      "remediation": "Update to latest version"
    }
  ],
  "summary": {
    "critical": 2,
    "high": 5,
    "medium": 8,
    "low": 12
  }
}`,
  },
  {
    method: 'POST',
    path: '/api/v1/agents/execute',
    name: 'Execute Agent',
    description: 'Execute AI agent with custom instructions',
    auth: true,
    request: `{
  "agent_type": "researcher",
  "target": "example.com",
  "instructions": "Perform comprehensive reconnaissance",
  "constraints": {
    "max_tools": 5,
    "timeout": 1800
  }
}`,
    response: `{
  "execution_id": "exec_xyz789",
  "agent_type": "researcher",
  "status": "executing",
  "tasks": [
    {
      "task_id": "task_001",
      "tool": "subfinder",
      "status": "completed",
      "result": "Found 15 subdomains"
    }
  ]
}`,
  },
];

const websocketEvents = [
  {
    event: 'scan.started',
    description: 'Emitted when a scan begins execution',
    payload: `{
  "scan_id": "scan_abc123",
  "target": "example.com",
  "timestamp": "2026-02-19T10:30:00Z"
}`,
  },
  {
    event: 'scan.progress',
    description: 'Real-time scan progress updates',
    payload: `{
  "scan_id": "scan_abc123",
  "progress": 65,
  "current_tool": "nuclei",
  "message": "Running vulnerability checks..."
}`,
  },
  {
    event: 'scan.finding',
    description: 'Emitted when a new finding is discovered',
    payload: `{
  "scan_id": "scan_abc123",
  "finding": {
    "severity": "high",
    "tool": "nuclei",
    "title": "CVE-2023-XXXX"
  }
}`,
  },
  {
    event: 'scan.completed',
    description: 'Emitted when scan finishes',
    payload: `{
  "scan_id": "scan_abc123",
  "status": "completed",
  "findings_count": 27,
  "duration": 2700
}`,
  },
];

export function APIDocs() {
  const [isVisible, setIsVisible] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
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

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET':
        return 'text-green-400 bg-green-400/10';
      case 'POST':
        return 'text-blue-400 bg-blue-400/10';
      case 'PUT':
        return 'text-yellow-400 bg-yellow-400/10';
      case 'DELETE':
        return 'text-red-400 bg-red-400/10';
      default:
        return 'text-slate-400 bg-slate-400/10';
    }
  };

  return (
    <section
      id="api"
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
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-medium mb-6">
            <Code className="w-4 h-4" />
            <span>API Reference</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            RESTful API &
            <br />
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              WebSocket Events
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Integrate Zen-AI-Pentest into your workflow with our comprehensive API.
            Real-time updates via WebSocket for live scan monitoring.
          </p>
        </div>

        {/* API Documentation */}
        <div
          className={`transition-all duration-700 delay-100 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <Tabs defaultValue="endpoints" className="w-full">
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-2 mb-8 bg-slate-900/50 border border-slate-800/50">
              <TabsTrigger
                value="endpoints"
                className="data-[state=active]:bg-slate-800 data-[state=active]:text-white"
              >
                <Globe className="w-4 h-4 mr-2" />
                REST Endpoints
              </TabsTrigger>
              <TabsTrigger
                value="websocket"
                className="data-[state=active]:bg-slate-800 data-[state=active]:text-white"
              >
                <Zap className="w-4 h-4 mr-2" />
                WebSocket Events
              </TabsTrigger>
            </TabsList>

            <TabsContent value="endpoints" className="space-y-6">
              {apiEndpoints.map((endpoint, index) => (
                <div
                  key={index}
                  className="rounded-xl bg-slate-900/50 border border-slate-800/50 overflow-hidden"
                >
                  {/* Endpoint Header */}
                  <div className="p-4 border-b border-slate-800/50 flex flex-wrap items-center gap-4">
                    <span
                      className={`px-3 py-1 rounded-lg text-sm font-mono font-bold ${getMethodColor(
                        endpoint.method
                      )}`}
                    >
                      {endpoint.method}
                    </span>
                    <code className="text-cyan-400 font-mono text-sm">
                      {endpoint.path}
                    </code>
                    {endpoint.auth && (
                      <span className="ml-auto flex items-center gap-1 text-xs text-slate-500">
                        <Lock className="w-3 h-3" />
                        Auth Required
                      </span>
                    )}
                  </div>

                  {/* Endpoint Content */}
                  <div className="p-4">
                    <h4 className="font-semibold text-white mb-2">
                      {endpoint.name}
                    </h4>
                    <p className="text-slate-400 text-sm mb-4">
                      {endpoint.description}
                    </p>

                    {/* Request/Response */}
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-slate-500 uppercase">
                            Request
                          </span>
                          <button
                            onClick={() =>
                              copyToClipboard(endpoint.request, index * 2)
                            }
                            className="text-slate-500 hover:text-white transition-colors"
                          >
                            {copiedIndex === index * 2 ? (
                              <Check className="w-4 h-4 text-green-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800/50 text-xs text-slate-300 overflow-x-auto">
                          <code>{endpoint.request}</code>
                        </pre>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-slate-500 uppercase">
                            Response
                          </span>
                          <button
                            onClick={() =>
                              copyToClipboard(endpoint.response, index * 2 + 1)
                            }
                            className="text-slate-500 hover:text-white transition-colors"
                          >
                            {copiedIndex === index * 2 + 1 ? (
                              <Check className="w-4 h-4 text-green-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800/50 text-xs text-slate-300 overflow-x-auto">
                          <code>{endpoint.response}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="websocket" className="space-y-6">
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/50 mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <Bell className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-white">
                      WebSocket Connection
                    </h4>
                    <code className="text-sm text-cyan-400">
                      wss://api.zen-ai-pentest.io/v1/ws
                    </code>
                  </div>
                </div>
                <p className="text-slate-400 text-sm">
                  Connect to receive real-time scan updates. Authenticate using
                  your JWT token in the connection query parameter.
                </p>
              </div>

              {websocketEvents.map((event, index) => (
                <div
                  key={index}
                  className="rounded-xl bg-slate-900/50 border border-slate-800/50 overflow-hidden"
                >
                  <div className="p-4 border-b border-slate-800/50">
                    <code className="text-purple-400 font-mono text-sm">
                      {event.event}
                    </code>
                    <p className="text-slate-400 text-sm mt-1">
                      {event.description}
                    </p>
                  </div>
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-slate-500 uppercase">
                        Payload
                      </span>
                      <button
                        onClick={() =>
                          copyToClipboard(event.payload, 100 + index)
                        }
                        className="text-slate-500 hover:text-white transition-colors"
                      >
                        {copiedIndex === 100 + index ? (
                          <Check className="w-4 h-4 text-green-400" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800/50 text-xs text-slate-300 overflow-x-auto">
                      <code>{event.payload}</code>
                    </pre>
                  </div>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </div>

        {/* API Base URL */}
        <div
          className={`mt-8 p-6 rounded-xl bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-500/20 transition-all duration-700 delay-200 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h4 className="font-semibold text-white mb-1">Base URL</h4>
              <code className="text-cyan-400">https://api.zen-ai-pentest.io/v1</code>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="border-slate-600 text-slate-300 hover:bg-slate-800/50"
                onClick={() =>
                  copyToClipboard('https://api.zen-ai-pentest.io/v1', 999)
                }
              >
                {copiedIndex === 999 ? (
                  <Check className="w-4 h-4 mr-2 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4 mr-2" />
                )}
                Copy URL
              </Button>
              <Button className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white border-0">
                <Terminal className="w-4 h-4 mr-2" />
                View Full Docs
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
