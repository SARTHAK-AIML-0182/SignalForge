import type { NovaAgentStatus, Signal, PublishedPost, RejectedTopic, DataSource, ActivityEvent } from '../types';

export const mockNovaStatus: NovaAgentStatus = {
  designation: 'NOVA-8824',
  personaName: 'NOVA',
  role: 'Autonomous Technology Signal Analyst',
  state: 'SCANNING',
  confidenceScore: 97.4,
  lastCycleAt: '14:45:10 IST',
  nextCycleAt: '15:00:00 IST',
  activeModels: ['Gemini 3.6 Pro Deep Reasoner', 'SignalForge Lattice Embedding v4'],
  cpuLoad: 34.2,
  memoryUsage: 61.8,
  activeThreads: 16,
  currentObjective: 'Analyzing post-quantum cryptographic primitives & liquid neural net benchmark telemetry.',
  totalSignalsProcessed24h: 1428,
};

export const mockSignals: Signal[] = [
  {
    id: 'sig-001',
    title: 'Zero-Shot Reasoning in Liquid Neural Networks for Sub-millisecond Control',
    summary: 'A new paper demonstrates continuous-time recurrent neural networks outperforming standard transformers in robotics precision and micro-agent latency by 4.2x.',
    source: 'arXiv:2608.04912',
    sourceType: 'arXiv',
    url: 'https://arxiv.org/abs/2608.04912',
    velocityScore: 94,
    relevanceScore: 9.6,
    sentiment: 'bullish',
    discoveredAt: '12 mins ago',
    tags: ['Liquid AI', 'Robotics', 'Zero-Shot', 'Edge Computing'],
    rawTelemetry: {
      citationCount: 42,
      growthRate: '+310% acceleration',
      impactFactor: 'High Tech Breakthrough',
    },
  },
  {
    id: 'sig-002',
    title: 'Rust Core Engine for Distributed Agent Memory Synchronization (v0.12 Release)',
    summary: 'Open-source release providing lock-free CRDT data structures for real-time memory sharing across thousands of multi-agent LLM clusters.',
    source: 'GitHub: agentic-labs/sync-mesh',
    sourceType: 'GitHub',
    url: 'https://github.com/agentic-labs/sync-mesh',
    velocityScore: 88,
    relevanceScore: 9.1,
    sentiment: 'bullish',
    discoveredAt: '28 mins ago',
    tags: ['Rust', 'Multi-Agent', 'Distributed Systems', 'CRDT'],
    rawTelemetry: {
      starsCount: 3840,
      growthRate: '+890 stars today',
    },
  },
  {
    id: 'sig-003',
    title: 'NIST Standardizes Post-Quantum Kyber-1024 Implementation for Browser Micro-kernels',
    summary: 'WebAssembly implementation of NIST Module-Lattice Key Encapsulation enables zero-overhead encrypted RPCs directly inside web browser workers.',
    source: 'HackerNews Top #2',
    sourceType: 'HackerNews',
    url: 'https://news.ycombinator.com/item?id=4091823',
    velocityScore: 82,
    relevanceScore: 8.8,
    sentiment: 'bullish',
    discoveredAt: '45 mins ago',
    tags: ['Security', 'Post-Quantum', 'Wasm', 'Cryptography'],
    rawTelemetry: {
      upvotes: 612,
      growthRate: 'Top Trending',
    },
  },
  {
    id: 'sig-004',
    title: 'Synthetic Data Collapse Mitigations using Entropy-Weighted Replay Buffers',
    summary: 'Researchers demonstrate a technique preventing generative model degradation when trained on recursively generated AI synthetic datasets.',
    source: 'arXiv:2608.03104',
    sourceType: 'arXiv',
    url: 'https://arxiv.org/abs/2608.03104',
    velocityScore: 76,
    relevanceScore: 8.5,
    sentiment: 'neutral',
    discoveredAt: '1 hour ago',
    tags: ['LLM Training', 'Synthetic Data', 'Entropy', 'Alignment'],
    rawTelemetry: {
      citationCount: 18,
      impactFactor: 'Crucial Foundation',
    },
  },
  {
    id: 'sig-005',
    title: 'GPU Memory Pooling via CXL 3.1: Hardware Benchmark Report',
    summary: 'First independent benchmarks showing Compute Express Link 3.1 enabling pooled GPU memory across nodes with sub-200ns memory access overhead.',
    source: 'TechCrunch Enterprise',
    sourceType: 'TechCrunch',
    url: 'https://techcrunch.com/hardware-cxl-gpu',
    velocityScore: 71,
    relevanceScore: 8.2,
    sentiment: 'bullish',
    discoveredAt: '2 hours ago',
    tags: ['Hardware', 'CXL', 'GPU Architecture', 'Infrastructure'],
    rawTelemetry: {
      impactFactor: 'Hardware Milestone',
    },
  },
];

export const mockPublishedPosts: PublishedPost[] = [
  {
    id: 'pub-101',
    title: 'The Shift to Liquid Neural Architectures: Why Transformers are Facing Edge Constraints',
    summary: 'As autonomous AI agents migrate to micro-drones, robotics, and edge control systems, traditional attention mechanisms encounter memory walls. Liquid Neural Networks offer continuous-time adaptivity with 90% less compute power.',
    content: `## Technology Intelligence Briefing #104

**Analyst:** NOVA (SignalForge Agent)  
**Confidence Index:** 9.6 / 10  

### Executive Summary
Recent telemetry from arXiv papers and hardware benchmarks indicates a significant inflection point in edge AI architecture. While Transformer attention mechanisms dominate cloud LLMs, **Liquid Neural Networks (LNNs)** operate via continuous differential equations rather than discrete time steps, yielding dynamic adaptability under resource constraints.

### Key Technical Breakthroughs
1. **Continuous-Time Dynamics**: LNN parameters adjust dynamically during inference based on incoming sensor stream flux.
2. **Sub-millisecond Latency**: 4.2x faster response time in closed-loop control tasks compared to lightweight ViTs.
3. **90% Footprint Reduction**: Running full zero-shot motor policies in under 12MB RAM.

### Strategic Recommendations
- **Platform Engineers**: Evaluate LNN micro-kernels for real-time sensor processing pipelines.
- **AI Infrastructure Teams**: Maintain hybrid architectures—LLMs for high-level reasoning, LNNs for real-time execution.`,
    channels: ['Newsletter', 'Telegram', 'Internal HUD'],
    publishedAt: 'Today, 14:15 IST',
    editorialScore: {
      overall: 9.5,
      novelty: 9.8,
      technicalDepth: 9.4,
      validity: 9.6,
      clarity: 9.2,
      actionability: 9.5,
    },
    publishingRationale: 'Signal velocity across arXiv and GitHub repositories exceeded the 90th percentile. Novelty score is high due to recent experimental validation on physical robotics hardware.',
    targetAudience: 'CTOs, AI Infrastructure Engineers & Robotics Researchers',
    keyTakeaways: [
      'Liquid Neural Networks solve memory wall issues for physical AI edge devices.',
      '4.2x faster real-time decision loops than standard transformer models.',
      'Hybrid cloud-edge AI paradigm is becoming the standard for 2026 systems.',
    ],
    sourceSignalIds: ['sig-001'],
    readTime: '4 min read',
    viewsCount: 1420,
  },
  {
    id: 'pub-102',
    title: 'Lock-Free CRDTs in Rust: Solving Multi-Agent Memory Drift in Distributed LLM Systems',
    summary: 'Autonomous AI swarms require high-speed, conflict-free state synchronization. We analyze the architecture behind sync-mesh v0.12 and how lock-free CRDT structures eliminate memory inconsistency.',
    content: `## Technology Intelligence Briefing #103

**Analyst:** NOVA (SignalForge Agent)  
**Confidence Index:** 9.2 / 10  

### The Problem with Multi-Agent Memory
When hundreds of autonomous agents perform concurrent tasks, central database locking introduces prohibitive latency bottlenecks and race conditions.

### The CRDT Solution
By leveraging Conflict-free Replicated Data Types implemented in Rust, multi-agent systems achieve eventual consistency across heterogeneous compute nodes without central coordination locks.`,
    channels: ['X/Twitter', 'Telegram', 'Internal HUD'],
    publishedAt: 'Yesterday, 18:30 IST',
    editorialScore: {
      overall: 9.1,
      novelty: 9.0,
      technicalDepth: 9.6,
      validity: 9.2,
      clarity: 8.9,
      actionability: 8.8,
    },
    publishingRationale: 'High open-source GitHub velocity (+890 stars in 24 hours) verified with clean code benchmarks and multi-agent architecture relevance.',
    targetAudience: 'Distributed Systems Engineers, AI Swarm Developers',
    keyTakeaways: [
      'Lock-free CRDT synchronization resolves multi-agent state race conditions.',
      'Zero central database bottlenecks for swarm topologies.',
    ],
    sourceSignalIds: ['sig-002'],
    readTime: '3 min read',
    viewsCount: 2890,
  },
];

export const mockRejectedTopics: RejectedTopic[] = [
  {
    id: 'rej-301',
    topic: 'Generic Prompt Engineering Cheat Sheet for 2026',
    source: 'Tech Community Blog',
    rejectedAt: '14:22:04 IST',
    rejectionReason: 'Fails novelty threshold score (< 3.0/10). Topic contains repetitive advice already published in 14 previous intelligence briefings.',
    noiseCategory: 'Low Novelty',
    similarityScore: 94,
  },
  {
    id: 'rej-302',
    topic: 'Unverified Rumor: Proprietary 100k GPU Cluster Outage',
    source: 'Social Media Speculation Stream',
    rejectedAt: '13:58:19 IST',
    rejectionReason: 'Fails verification score (< 4.0/10). No corroborating telemetry from official status pages or hardware vendor telemetry.',
    noiseCategory: 'Unverified Speculation',
    similarityScore: 42,
  },
  {
    id: 'rej-303',
    topic: 'AI Startup XYZ Raises $5M for Generic SaaS Wrapper',
    source: 'PR Newswire Digest',
    rejectedAt: '12:40:11 IST',
    rejectionReason: 'Fails technical depth score (< 2.5/10). Pure commercial funding PR without open benchmarks, architecture novelties, or technical artifacts.',
    noiseCategory: 'Marketing Hype',
    similarityScore: 78,
  },
  {
    id: 'rej-304',
    topic: 'Quantum-Resistant Lattice Cryptography - Duplicate Signal',
    source: 'arXiv Secondary Feed',
    rejectedAt: '11:15:33 IST',
    rejectionReason: 'Duplicate of Signal sig-003 already processed and included in intelligence pipeline.',
    noiseCategory: 'Duplicate',
    similarityScore: 98,
  },
];

export const mockDataSources: DataSource[] = [
  {
    id: 'src-1',
    name: 'arXiv CS & AI Preprints',
    type: 'Research API',
    status: 'HEALTHY',
    reliabilityScore: 99.4,
    lastSync: '3 mins ago',
    signalCount24h: 482,
    avgLatency: '140ms',
  },
  {
    id: 'src-2',
    name: 'GitHub Trending & Releases',
    type: 'Code Repository',
    status: 'HEALTHY',
    reliabilityScore: 98.9,
    lastSync: '1 min ago',
    signalCount24h: 620,
    avgLatency: '95ms',
  },
  {
    id: 'src-3',
    name: 'HackerNews Algolia Pipeline',
    type: 'Community Forum',
    status: 'HEALTHY',
    reliabilityScore: 97.2,
    lastSync: 'Just now',
    signalCount24h: 215,
    avgLatency: '45ms',
  },
  {
    id: 'src-4',
    name: 'ProductHunt Tech Radar',
    type: 'News Aggregator',
    status: 'SYNCING',
    reliabilityScore: 94.0,
    lastSync: '12 mins ago',
    signalCount24h: 64,
    avgLatency: '320ms',
  },
  {
    id: 'src-5',
    name: 'Twitter/X AI Research Stream',
    type: 'Social Telemetry',
    status: 'DEGRADED',
    reliabilityScore: 86.5,
    lastSync: '22 mins ago',
    signalCount24h: 47,
    avgLatency: '1.2s',
  },
];

export const mockActivityTimeline: ActivityEvent[] = [
  {
    id: 'act-501',
    timestamp: '14:45:10 IST',
    type: 'INGESTION',
    title: 'Ingestion Cycle Completed',
    detail: 'Processed 148 new paper abstracts & repository releases across 5 active data streams.',
    status: 'success',
  },
  {
    id: 'act-502',
    timestamp: '14:38:00 IST',
    type: 'EVALUATION',
    title: 'Signal Velocity Spike Detected',
    detail: 'Detected +310% acceleration on Liquid Neural Networks paper (arXiv:2608.04912). Assigned high priority.',
    status: 'info',
  },
  {
    id: 'act-503',
    timestamp: '14:22:04 IST',
    type: 'REJECTION',
    title: 'Filtered Noise Candidate',
    detail: 'Rejected "Generic Prompt Engineering Cheat Sheet" (94% similarity score with published briefing #088).',
    status: 'warning',
  },
  {
    id: 'act-504',
    timestamp: '14:15:00 IST',
    type: 'PUBLICATION',
    title: 'Published Briefing #104',
    detail: 'Broadcasted briefing on Liquid Neural Architectures to Newsletter, Telegram, and Internal HUD.',
    status: 'success',
  },
  {
    id: 'act-505',
    timestamp: '14:00:00 IST',
    type: 'SYNTHESIS',
    title: 'Synthesized Intelligence Draft',
    detail: 'Gemini 3.6 Pro synthesized 4-page briefing with 9.5 overall editorial score.',
    status: 'success',
  },
];
