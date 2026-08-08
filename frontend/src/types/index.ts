export type AgentState = 'SCANNING' | 'ANALYZING' | 'SYNTHESIZING' | 'PUBLISHING' | 'IDLE';

export interface NovaAgentStatus {
  designation: string;
  personaName: string;
  role: string;
  state: AgentState;
  confidenceScore: number;
  lastCycleAt: string;
  nextCycleAt: string;
  activeModels: string[];
  cpuLoad: number;
  memoryUsage: number;
  activeThreads: number;
  currentObjective: string;
  totalSignalsProcessed24h: number;
}

export interface Signal {
  id: string;
  title: string;
  summary: string;
  source: string;
  sourceType: 'arXiv' | 'GitHub' | 'HackerNews' | 'ProductHunt' | 'TechCrunch' | 'Twitter';
  url: string;
  velocityScore: number; // 0-100 scale
  relevanceScore: number; // 0-10 scale
  sentiment: 'bullish' | 'neutral' | 'bearish';
  discoveredAt: string;
  tags: string[];
  rawTelemetry: {
    citationCount?: number;
    starsCount?: number;
    upvotes?: number;
    growthRate?: string;
    impactFactor?: string;
  };
}

export interface EditorialScore {
  overall: number; // 0-10
  novelty: number; // 0-10
  technicalDepth: number; // 0-10
  validity: number; // 0-10
  clarity: number; // 0-10
  actionability: number; // 0-10
}

export interface PublishedPost {
  id: string;
  title: string;
  summary: string;
  content: string;
  channels: ('Telegram' | 'X/Twitter' | 'Newsletter' | 'Internal HUD')[];
  publishedAt: string;
  editorialScore: EditorialScore;
  publishingRationale: string;
  targetAudience: string;
  keyTakeaways: string[];
  sourceSignalIds: string[];
  readTime: string;
  viewsCount: number;
}

export interface RejectedTopic {
  id: string;
  topic: string;
  source: string;
  rejectedAt: string;
  rejectionReason: string;
  noiseCategory: 'Duplicate' | 'Low Novelty' | 'Marketing Hype' | 'Unverified Speculation' | 'Out of Domain';
  similarityScore: number; // % match to existing posts
}

export interface DataSource {
  id: string;
  name: string;
  type: 'Research API' | 'Code Repository' | 'Community Forum' | 'News Aggregator' | 'Social Telemetry';
  status: 'HEALTHY' | 'SYNCING' | 'DEGRADED';
  reliabilityScore: number; // percentage
  lastSync: string;
  signalCount24h: number;
  avgLatency: string;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: 'INGESTION' | 'EVALUATION' | 'REJECTION' | 'SYNTHESIS' | 'PUBLICATION' | 'SYSTEM';
  title: string;
  detail: string;
  status: 'success' | 'warning' | 'info' | 'error';
}
