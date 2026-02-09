// ============================================
// Zen-AI-Pentest Framework - Type Definitions
// ============================================

// Scan Types
export interface Scan {
  id: string;
  name: string;
  target: string;
  status: ScanStatus;
  type: ScanType;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
  progress: number;
  findingsCount: number;
  agents: string[];
  metadata?: Record<string, unknown>;
}

export type ScanStatus = 
  | 'pending' 
  | 'running' 
  | 'paused' 
  | 'completed' 
  | 'failed' 
  | 'cancelled';

export type ScanType = 
  | 'network' 
  | 'web' 
  | 'api' 
  | 'infrastructure' 
  | 'full';

// Finding Types
export interface Finding {
  id: string;
  scanId: string;
  title: string;
  description: string;
  severity: SeverityLevel;
  confidence: ConfidenceLevel;
  category: string;
  status: FindingStatus;
  cvssScore?: number;
  riskScore: number;
  target: string;
  port?: number;
  service?: string;
  cveIds?: string[];
  references?: string[];
  remediation?: string;
  notes?: string;
  evidence: Evidence[];
  createdAt: string;
  updatedAt: string;
  validatedBy?: string;
  isFalsePositive: boolean;
}

export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type ConfidenceLevel = 'confirmed' | 'high' | 'medium' | 'low';
export type FindingStatus = 'open' | 'in_review' | 'validated' | 'resolved' | 'false_positive';

// Evidence Types
export interface Evidence {
  id: string;
  findingId: string;
  type: EvidenceType;
  content: string;
  metadata: EvidenceMetadata;
  createdAt: string;
}

export type EvidenceType = 
  | 'screenshot' 
  | 'http_response' 
  | 'pcap' 
  | 'video' 
  | 'log' 
  | 'file';

export interface EvidenceMetadata {
  filename?: string;
  size?: number;
  mimeType?: string;
  url?: string;
  dimensions?: { width: number; height: number };
  duration?: number;
  timestamp?: string;
}

// Agent Types
export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  capabilities: string[];
  currentTask?: string;
  lastHeartbeat: string;
  metrics: AgentMetrics;
  version: string;
}

export type AgentType = 
  | 'recon' 
  | 'scanner' 
  | 'exploitation' 
  | 'post_exploitation' 
  | 'ai_analyzer';

export type AgentStatus = 
  | 'idle' 
  | 'busy' 
  | 'offline' 
  | 'error';

export interface AgentMetrics {
  tasksCompleted: number;
  tasksFailed: number;
  averageTaskDuration: number;
  cpuUsage?: number;
  memoryUsage?: number;
}

// Attack Graph Types
export interface AttackGraph {
  nodes: AttackNode[];
  edges: AttackEdge[];
}

export interface AttackNode {
  id: string;
  type: NodeType;
  label: string;
  data: NodeData;
  position?: { x: number; y: number };
}

export type NodeType = 
  | 'host' 
  | 'service' 
  | 'vulnerability' 
  | 'credential' 
  | 'data';

export interface NodeData {
  ip?: string;
  hostname?: string;
  port?: number;
  service?: string;
  version?: string;
  cve?: string;
  cvss?: number;
  severity?: SeverityLevel;
  [key: string]: unknown;
}

export interface AttackEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  label?: string;
}

export type EdgeType = 
  | 'connection' 
  | 'exploit' 
  | 'depends' 
  | 'leads_to';

// Report Types
export interface Report {
  id: string;
  scanId: string;
  name: string;
  format: ReportFormat;
  status: ReportStatus;
  content?: string;
  url?: string;
  createdAt: string;
  generatedAt?: string;
  size?: number;
}

export type ReportFormat = 
  | 'markdown' 
  | 'html' 
  | 'pdf' 
  | 'json' 
  | 'xml';

export type ReportStatus = 
  | 'pending' 
  | 'generating' 
  | 'completed' 
  | 'failed';

// Timeline Types
export interface TimelineEvent {
  id: string;
  scanId: string;
  type: EventType;
  title: string;
  description?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export type EventType = 
  | 'scan_started' 
  | 'scan_completed' 
  | 'finding_discovered' 
  | 'agent_assigned' 
  | 'agent_completed' 
  | 'milestone_reached' 
  | 'alert';

// Alert Types
export interface Alert {
  id: string;
  type: AlertType;
  severity: SeverityLevel;
  title: string;
  message: string;
  findingId?: string;
  scanId?: string;
  acknowledged: boolean;
  createdAt: string;
}

export type AlertType = 
  | 'critical_finding' 
  | 'scan_failed' 
  | 'agent_offline' 
  | 'high_risk';

// Statistics Types
export interface ScanStatistics {
  totalScans: number;
  activeScans: number;
  completedScans: number;
  failedScans: number;
  findingsBySeverity: Record<SeverityLevel, number>;
  findingsByCategory: Record<string, number>;
  scansByType: Record<ScanType, number>;
  averageScanDuration: number;
  topTargets: Array<{ target: string; count: number }>;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: MessageType;
  payload: unknown;
  timestamp: string;
}

export type MessageType = 
  | 'scan_update' 
  | 'finding_update' 
  | 'agent_update' 
  | 'alert' 
  | 'heartbeat';

// Filter Types
export interface FindingsFilter {
  severity?: SeverityLevel[];
  status?: FindingStatus[];
  category?: string[];
  confidence?: ConfidenceLevel[];
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}
