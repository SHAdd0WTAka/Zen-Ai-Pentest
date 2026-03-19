// ============================================
// ZEN-AI-PENTEST TYPE DEFINITIONS
// ============================================

// User & Authentication Types
export interface User {
  id: string;
  email: string;
  username: string;
  fullName: string;
  avatar?: string;
  role: UserRole;
  isActive: boolean;
  lastLogin: string;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = 'admin' | 'analyst' | 'viewer';

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  fullName: string;
}

// Scan Types
export interface Scan {
  id: string;
  name: string;
  description?: string;
  target: string;
  type: ScanType;
  status: ScanStatus;
  progress: number;
  config: ScanConfig;
  findings: number;
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
  infoCount: number;
  createdBy: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
}

export type ScanType =
  | 'network'
  | 'web'
  | 'api'
  | 'infrastructure'
  | 'compliance'
  | 'full';

export type ScanStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface ScanConfig {
  tools: string[];
  ports?: string;
  threads?: number;
  timeout?: number;
  headers?: Record<string, string>;
  cookies?: string;
  followRedirects?: boolean;
  sslVerification?: boolean;
  customOptions?: Record<string, unknown>;
}

export interface ScanTemplate {
  id: string;
  name: string;
  description: string;
  type: ScanType;
  config: ScanConfig;
  isDefault: boolean;
  createdBy: string;
  createdAt: string;
}

// Vulnerability Types
export interface Vulnerability {
  id: string;
  scanId: string;
  name: string;
  description: string;
  severity: Severity;
  cvssScore: number;
  cvssVector?: string;
  cveId?: string;
  cweId?: string;
  owaspCategory?: string;
  proofOfConcept?: string;
  remediation: string;
  references: string[];
  affectedHosts: AffectedHost[];
  tags: string[];
  status: VulnerabilityStatus;
  assignedTo?: string;
  verifiedBy?: string;
  verifiedAt?: string;
  falsePositiveReason?: string;
  createdAt: string;
  updatedAt: string;
}

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type VulnerabilityStatus =
  | 'open'
  | 'in_progress'
  | 'resolved'
  | 'false_positive'
  | 'risk_accepted';

export interface AffectedHost {
  host: string;
  port?: number;
  service?: string;
  evidence: string;
  request?: string;
  response?: string;
}

// Asset Types
export interface Asset {
  id: string;
  type: AssetType;
  value: string;
  organization?: string;
  description?: string;
  tags: string[];
  firstSeen: string;
  lastSeen: string;
  scanCount: number;
  vulnerabilityCount: number;
  services: Service[];
  isActive: boolean;
}

export type AssetType = 'domain' | 'ip' | 'subnet' | 'url' | 'application';

export interface Service {
  port: number;
  protocol: 'tcp' | 'udp';
  name: string;
  version?: string;
  banner?: string;
  state: 'open' | 'closed' | 'filtered';
}

// Report Types
export interface Report {
  id: string;
  name: string;
  description?: string;
  type: ReportType;
  format: ReportFormat;
  scanId?: string;
  templateId?: string;
  status: ReportStatus;
  fileUrl?: string;
  fileSize?: number;
  generatedBy: string;
  generatedAt?: string;
  createdAt: string;
  expiresAt?: string;
}

export type ReportType =
  | 'executive'
  | 'technical'
  | 'compliance'
  | 'remediation'
  | 'custom';

export type ReportFormat = 'pdf' | 'html' | 'json' | 'xml' | 'csv';

export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed';

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  type: ReportType;
  format: ReportFormat;
  content: string;
  isDefault: boolean;
  createdBy: string;
  createdAt: string;
}

// Agent Types
export interface Agent {
  id: string;
  name: string;
  hostname: string;
  ipAddress: string;
  version: string;
  status: AgentStatus;
  capabilities: string[];
  currentTask?: string;
  lastHeartbeat: string;
  tasksCompleted: number;
  tasksFailed: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  createdAt: string;
  updatedAt: string;
}

export type AgentStatus = 'online' | 'offline' | 'busy' | 'error';

// Dashboard Types
export interface DashboardStats {
  totalScans: number;
  activeScans: number;
  totalVulnerabilities: number;
  criticalVulnerabilities: number;
  highVulnerabilities: number;
  mediumVulnerabilities: number;
  lowVulnerabilities: number;
  totalAssets: number;
  onlineAgents: number;
  recentScans: Scan[];
  recentVulnerabilities: Vulnerability[];
  scanTrend: TrendData[];
  vulnerabilityTrend: TrendData[];
}

export interface TrendData {
  date: string;
  value: number;
}

export interface SeverityDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

// WebSocket Types
export interface WebSocketMessage {
  type: MessageType;
  payload: unknown;
  timestamp: string;
}

export type MessageType =
  | 'scan_update'
  | 'scan_progress'
  | 'scan_completed'
  | 'scan_failed'
  | 'vulnerability_found'
  | 'agent_status'
  | 'notification'
  | 'ping'
  | 'pong';

export interface ScanProgressMessage {
  scanId: string;
  progress: number;
  status: ScanStatus;
  currentTool?: string;
  message?: string;
  findingsCount: number;
}

// API Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  meta?: PaginationMeta;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

// Filter & Sort Types
export interface FilterParams {
  search?: string;
  severity?: Severity[];
  status?: string[];
  type?: string[];
  dateFrom?: string;
  dateTo?: string;
  tags?: string[];
}

export interface SortParams {
  field: string;
  order: 'asc' | 'desc';
}

// Notification Types
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  data?: Record<string, unknown>;
  isRead: boolean;
  createdAt: string;
}

export type NotificationType =
  | 'info'
  | 'success'
  | 'warning'
  | 'error'
  | 'critical';

// Settings Types
export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  dateFormat: string;
  notifications: NotificationSettings;
  dashboard: DashboardSettings;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  slack: boolean;
  scanCompleted: boolean;
  vulnerabilityFound: boolean;
  criticalAlert: boolean;
}

export interface DashboardSettings {
  defaultView: string;
  widgets: string[];
  refreshInterval: number;
}

// Compliance Types
export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  description: string;
  controls: ComplianceControl[];
}

export interface ComplianceControl {
  id: string;
  name: string;
  description: string;
  severity: Severity;
  requirements: string[];
}

// Tool Types
export interface SecurityTool {
  id: string;
  name: string;
  description: string;
  version: string;
  category: ToolCategory;
  command: string;
  arguments: ToolArgument[];
  outputFormat: 'json' | 'xml' | 'text' | 'csv';
  isInstalled: boolean;
  isEnabled: boolean;
}

export type ToolCategory =
  | 'scanner'
  | 'enumerator'
  | 'fuzzer'
  | 'detector'
  | 'analyzer';

export interface ToolArgument {
  name: string;
  flag: string;
  description: string;
  type: 'string' | 'number' | 'boolean' | 'array';
  required: boolean;
  default?: unknown;
}

// Workflow Types
export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  isActive: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  tool: string;
  config: Record<string, unknown>;
  dependsOn?: string[];
  condition?: string;
  timeout: number;
  retries: number;
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Nullable<T> = T | null;

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
