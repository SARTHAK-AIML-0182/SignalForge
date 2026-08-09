import { useState, useEffect, useRef } from 'react';
import {
  Header,
  NovaPersonaPanel,
  MetricCards,
  SignalFeed,
  PublishedPosts,
  RejectedTopics,
  SourcesGrid,
  ActivityTimeline,
  SignalModal,
} from './components';
import {
  mockNovaStatus,
  mockSignals,
  mockPublishedPosts,
  mockRejectedTopics,
  mockDataSources,
  mockActivityTimeline,
} from './mock/mockData';
import type { Signal, NovaAgentStatus, ActivityEvent, PublishedPost } from './types';
import { getFeed } from './services/agentApi';
import { getStoredAgentId, adaptFeedPosts } from './services/postAdapter';
import { LayoutDashboard, Radio, Send, FilterX, Network, Activity } from 'lucide-react';

export function App() {
  const [status, setStatus] = useState<NovaAgentStatus>(mockNovaStatus);
  const [signals, setSignals] = useState<Signal[]>(mockSignals);
  const [publishedPosts, setPublishedPosts] = useState<PublishedPost[]>(mockPublishedPosts);
  const [rejectedTopics] = useState(mockRejectedTopics);
  const [sources] = useState(mockDataSources);
  const [timeline, setTimeline] = useState<ActivityEvent[]>(mockActivityTimeline);

  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'SIGNALS' | 'PUBLISHED' | 'REJECTED' | 'SOURCES' | 'TIMELINE'>('OVERVIEW');
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [isScanning, setIsScanning] = useState<boolean>(false);

  const isFetchingRef = useRef(false);

  useEffect(() => {
    let isMounted = true;

    const fetchLiveFeed = async () => {
      const agentId = getStoredAgentId();
      if (!agentId) {
        console.warn(
          'SignalForge: No agent ID found in localStorage (signalforge_agent_id) or VITE_AGENT_ID env. Using fallback mock published posts.'
        );
        return;
      }

      if (isFetchingRef.current) return;
      isFetchingRef.current = true;

      try {
        const feedData = await getFeed(agentId);
        if (isMounted && feedData && Array.isArray(feedData.posts) && feedData.posts.length > 0) {
          const adaptedPosts = adaptFeedPosts(feedData.posts);
          if (adaptedPosts.length > 0) {
            setPublishedPosts(adaptedPosts);
          }
        }
      } catch (error) {
        console.warn('SignalForge: Failed to load live agent feed from backend, keeping fallback posts:', error);
      } finally {
        isFetchingRef.current = false;
      }
    };

    fetchLiveFeed();

    const intervalId = setInterval(() => {
      fetchLiveFeed();
    }, 30000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  // Trigger manual force scan simulation
  const handleTriggerScan = () => {
    setIsScanning(true);
    setStatus((prev) => ({ ...prev, state: 'SCANNING' }));

    setTimeout(() => {
      // Simulate discovering a new signal
      const newSignal: Signal = {
        id: `sig-00${signals.length + 1}`,
        title: 'Quantum-Resistant Lattice Key Encapsulation in Edge WebAssembly',
        summary: 'Newly ingested telemetry from arXiv shows 9.8 relevance score in post-quantum browser micro-kernels.',
        source: 'arXiv:2608.09911',
        sourceType: 'arXiv',
        url: 'https://arxiv.org/abs/2608.09911',
        velocityScore: 97,
        relevanceScore: 9.8,
        sentiment: 'bullish',
        discoveredAt: 'Just now',
        tags: ['Post-Quantum', 'Wasm', 'Cryptography', 'Zero-Trust'],
        rawTelemetry: {
          citationCount: 12,
          impactFactor: 'Immediate Breakthrough',
        },
      };

      const newTimelineEvent: ActivityEvent = {
        id: `act-${Date.now()}`,
        timestamp: 'Just now',
        type: 'INGESTION',
        title: 'Manual Cycle Execution Completed',
        detail: 'Discovered 1 new high-confidence signal and updated vector embeddings.',
        status: 'success',
      };

      setSignals((prev) => [newSignal, ...prev]);
      setTimeline((prev) => [newTimelineEvent, ...prev]);
      setStatus((prev) => ({
        ...prev,
        state: 'IDLE',
        lastCycleAt: 'Just now',
        totalSignalsProcessed24h: prev.totalSignalsProcessed24h + 1,
      }));
      setIsScanning(false);
    }, 2500);
  };

  const navTabs = [
    { id: 'OVERVIEW', label: 'Overview HUD', icon: LayoutDashboard },
    { id: 'SIGNALS', label: `Signals (${signals.length})`, icon: Radio },
    { id: 'PUBLISHED', label: `Briefings (${publishedPosts.length})`, icon: Send },
    { id: 'REJECTED', label: `Rejected (${rejectedTopics.length})`, icon: FilterX },
    { id: 'SOURCES', label: `Sources (${sources.length})`, icon: Network },
    { id: 'TIMELINE', label: 'Activity Log', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 scanline-overlay flex flex-col">
      {/* Top Header */}
      <Header status={status} onTriggerScan={handleTriggerScan} isScanning={isScanning} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-6">
        
        {/* Navigation Tabs */}
        <nav className="flex items-center gap-2 overflow-x-auto pb-2 font-mono text-xs border-b border-slate-800">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-950 text-cyan-300 font-bold border border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Tab Content Rendering */}
        {activeTab === 'OVERVIEW' && (
          <div className="space-y-6">
            {/* NOVA Persona HUD */}
            <NovaPersonaPanel status={status} />

            {/* KPI Cards */}
            <MetricCards
              signalsCount={signals.length}
              rejectedCount={rejectedTopics.length}
              publishedCount={publishedPosts.length}
              avgEditorialScore={9.3}
            />

            {/* Combined Grid: Latest Signals + Recent Briefings */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7">
                <SignalFeed signals={signals} onSelectSignal={(sig) => setSelectedSignal(sig)} />
              </div>
              <div className="lg:col-span-5 space-y-6">
                <ActivityTimeline events={timeline.slice(0, 4)} />
                <SourcesGrid sources={sources.slice(0, 3)} />
              </div>
            </div>

            {/* Published Briefings Highlight */}
            <PublishedPosts posts={publishedPosts} />
          </div>
        )}

        {activeTab === 'SIGNALS' && (
          <SignalFeed signals={signals} onSelectSignal={(sig) => setSelectedSignal(sig)} />
        )}

        {activeTab === 'PUBLISHED' && (
          <PublishedPosts posts={publishedPosts} />
        )}

        {activeTab === 'REJECTED' && (
          <RejectedTopics rejectedTopics={rejectedTopics} />
        )}

        {activeTab === 'SOURCES' && (
          <SourcesGrid sources={sources} />
        )}

        {activeTab === 'TIMELINE' && (
          <ActivityTimeline events={timeline} />
        )}

      </main>

      {/* Signal Inspection Modal */}
      <SignalModal signal={selectedSignal} onClose={() => setSelectedSignal(null)} />

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-4 text-center text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>SignalForge — Autonomous AI Technology Intelligence Platform</span>
          <span className="text-slate-600">NOVA Agent Persona v2.4 • Hackathon Build</span>
        </div>
      </footer>
    </div>
  );
}
