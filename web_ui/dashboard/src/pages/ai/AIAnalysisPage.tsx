// ============================================
// Zen-AI-Pentest Platform - AI Analysis Page
// AI-Powered Security Analysis Interface
// ============================================

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Brain,
  MessageSquare,
  Send,
  Sparkles,
  Bug,
  FileText,
  Code,
  Loader2,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  History,
  Settings,
  Zap,
  Search,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { aiApi } from '@/services/api';

// ============================================
// Types
// ============================================
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    tokens?: number;
    confidence?: number;
    sources?: string[];
  };
}

interface AnalysisContext {
  type: 'vulnerability' | 'scan' | 'report' | 'code' | 'general';
  id?: string;
  name?: string;
}

interface AIInsight {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  confidence: number;
}

// ============================================
// Helper Components
// ============================================
const MarkdownComponents = {
  code({ node, inline, className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || '');
    return !inline && match ? (
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={match[1]}
        PreTag="div"
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
};

// ============================================
// Main Component
// ============================================
export function AIAnalysisPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'system',
      content: 'Welcome to Zen AI Security Assistant. I can help you analyze vulnerabilities, review code, interpret scan results, and provide security recommendations. How can I assist you today?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedContext, setSelectedContext] = useState<AnalysisContext>({ type: 'general' });
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch AI insights from API
  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['ai-insights'],
    queryFn: aiApi.getInsights,
  });

  // Fetch conversation history from API
  const { data: history } = useQuery({
    queryKey: ['ai-history'],
    queryFn: aiApi.getHistory,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: ({ message, context }: { message: string; context: AnalysisContext }) =>
      aiApi.analyze({ message, context, model: selectedModel }),
    onSuccess: (data) => {
      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        metadata: {
          model: selectedModel,
          tokens: data.tokens,
          confidence: data.confidence,
        },
      };
      setMessages((prev) => [...prev, aiMessage]);
    },
    onError: () => {
      toast.error('Failed to get AI response');
    },
  });

  const handleSend = async () => {
    if (!input.trim() || sendMessageMutation.isPending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    sendMessageMutation.mutate({ message: input, context: selectedContext });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success('Copied to clipboard');
  };

  const resetConversation = () => {
    setMessages([
      {
        id: '1',
        role: 'system',
        content: 'Welcome to Zen AI Security Assistant. I can help you analyze vulnerabilities, review code, interpret scan results, and provide security recommendations. How can I assist you today?',
        timestamp: new Date(),
      },
    ]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            AI Security Analysis
          </h1>
          <p className="text-muted-foreground">
            AI-powered vulnerability analysis and security insights
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-40">
              <Sparkles className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gpt-4">GPT-4</SelectItem>
              <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
              <SelectItem value="claude-3">Claude 3</SelectItem>
              <SelectItem value="local-llm">Local LLM</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Chat Interface */}
        <Card className="lg:col-span-2 flex flex-col h-[calc(100vh-280px)]">
          <CardHeader className="border-b py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-primary" />
                <CardTitle className="text-base">Security Assistant</CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Select
                  value={selectedContext.type}
                  onValueChange={(value: any) =>
                    setSelectedContext({ type: value })
                  }
                >
                  <SelectTrigger className="w-40 h-8 text-xs">
                    <SelectValue placeholder="Context" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="vulnerability">Vulnerability</SelectItem>
                    <SelectItem value="scan">Scan Results</SelectItem>
                    <SelectItem value="report">Report</SelectItem>
                    <SelectItem value="code">Code Review</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="ghost" size="sm" onClick={resetConversation}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'flex-row-reverse' : ''
                    }`}
                  >
                    <Avatar className={message.role === 'assistant' ? 'bg-primary' : 'bg-muted'}>
                      <AvatarFallback>
                        {message.role === 'assistant' ? (
                          <Brain className="h-4 w-4" />
                        ) : (
                          'U'
                        )}
                      </AvatarFallback>
                    </Avatar>
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown components={MarkdownComponents}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                      {message.metadata && (
                        <div className="mt-2 flex items-center gap-2 text-xs opacity-70">
                          <span>{message.metadata.model}</span>
                          <span>•</span>
                          <span>{message.metadata.tokens} tokens</span>
                          <span>•</span>
                          <span>{message.metadata.confidence}% confidence</span>
                        </div>
                      )}
                      {message.role === 'assistant' && (
                        <div className="mt-2 flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => copyToClipboard(message.content)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6">
                            <ThumbsUp className="h-3 w-3" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6">
                            <ThumbsDown className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {sendMessageMutation.isPending && (
                  <div className="flex gap-3">
                    <Avatar className="bg-primary">
                      <AvatarFallback>
                        <Brain className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="bg-muted rounded-lg p-3 flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Analyzing...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Textarea
                  placeholder="Ask about vulnerabilities, scan results, or security recommendations..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="min-h-[60px] resize-none"
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || sendMessageMutation.isPending}
                  className="px-3"
                >
                  {sendMessageMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                <Zap className="h-3 w-3" />
                <span>Pro tip: Try "Analyze my latest scan results" or "Review this code for SQL injection"</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => setInput('Analyze my latest vulnerability scan')}
              >
                <Search className="mr-2 h-4 w-4" />
                Analyze Latest Scan
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => setInput('Review code for security issues')}
              >
                <Code className="mr-2 h-4 w-4" />
                Code Security Review
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => setInput('Generate remediation report')}
              >
                <FileText className="mr-2 h-4 w-4" />
                Generate Report
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => setInput('Explain this vulnerability: CVE-2024-1234')}
              >
                <Bug className="mr-2 h-4 w-4" />
                Explain CVE
              </Button>
            </CardContent>
          </Card>

          {/* AI Insights */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-yellow-500" />
                AI Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              {insightsLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              ) : insights?.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No insights available
                </p>
              ) : (
                <div className="space-y-3">
                  {insights?.slice(0, 3).map((insight: AIInsight) => (
                    <div
                      key={insight.id}
                      className="p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() => setInput(`Tell me more about: ${insight.title}`)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium line-clamp-2">{insight.title}</p>
                        <Badge
                          variant={
                            insight.severity === 'critical'
                              ? 'destructive'
                              : insight.severity === 'high'
                                ? 'default'
                              : 'secondary'
                          }
                          className="text-xs shrink-0"
                        >
                          {insight.severity}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {insight.description}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs">
                          {insight.category}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {insight.confidence}% confidence
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent History */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <History className="h-4 w-4" />
                Recent Conversations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {history?.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No conversation history
                </p>
              ) : (
                <div className="space-y-2">
                  {history?.slice(0, 5).map((item: any, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 rounded hover:bg-muted cursor-pointer"
                    >
                      <span className="text-sm">{item.title}</span>
                      <span className="text-xs text-muted-foreground">{item.date}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
