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
  PersonaModal,
} from './components';
import {
  mockNovaStatus,
  mockSignals,
  mockPublishedPosts,
  mockRejectedTopics,
  mockDataSources,
  mockActivityTimeline,
} from './mock/mockData';
import type { Signal, NovaAgentStatus, ActivityEvent, PublishedPost, RejectedTopic } from './types';
import {
  initializeAgent,
  getFeed,
  runWorkflow,
  getWorkflows,
  inspectWorkflow,
  getPersona,
  updatePersona,
  getFeedConfig,
  updateFeedConfig,
  ApiError,
  type PersonaResponse,
  type PersonaUpdateRequest,
  type FeedConfigResponse,
  type WorkflowInspectionResponse,
  type WorkflowSummaryResponse,
} from './services/agentApi';
import { getStoredAgentId, setStoredAgentId, adaptFeedPosts } from './services/postAdapter';
import { LayoutDashboard, Radio, Send, FilterX, Network, Activity, AlertTriangle, CheckCircle2, ShieldAlert, X } from 'lucide-react';

export function App() {
  const [status, setStatus] = useState<NovaAgentStatus>(mockNovaStatus);
  const [signals] = useState<Signal[]>(mockSignals);
  const [publishedPosts, setPublishedPosts] = useState<PublishedPost[]>(mockPublishedPosts);
  const [rejectedTopics, setRejectedTopics] = useState<RejectedTopic[]>(mockRejectedTopics);
  const [sources] = useState(mockDataSources);
  const [timeline, setTimeline] = useState<ActivityEvent[]>(mockActivityTimeline);

  const [agentId, setAgentIdState] = useState<string | null>(getStoredAgentId());
  const [personaData, setPersonaData] = useState<PersonaResponse | null>(null);
  const [, setFeedConfig] = useState<FeedConfigResponse | null>(null);
  const [latestInspection, setLatestInspection] = useState<WorkflowInspectionResponse | null>(null);
  const [, setWorkflowHistory] = useState<WorkflowSummaryResponse[]>([]);

  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'SIGNALS' | 'PUBLISHED' | 'REJECTED' | 'SOURCES' | 'TIMELINE'>('OVERVIEW');
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [isPersonaModalOpen, setIsPersonaModalOpen] = useState<boolean>(false);

  const [banner, setBanner] = useState<{ type: 'info' | 'warning' | 'error' | 'success'; text: string; retryAfter?: number } | null>(null);

  const isFetchingRef = useRef(false);

  // Initialize Agent and Load Backend Telemetry
  useEffect(() => {
    let isMounted = true;

    const setupAgentAndLoad = async () => {
      if (isFetchingRef.current) return;
      isFetchingRef.current = true;

      let currentId = getStoredAgentId();

      // 1. Initialize Agent via POST /api/agent/init if no stored agent ID
      if (!currentId) {
        try {
          const initRes = await initializeAgent({
            persona: { name: 'NOVA', domain: 'AI & Emerging Technology' },
          });
          if (initRes && initRes.agentId) {
            currentId = initRes.agentId;
            setStoredAgentId(currentId);
            if (isMounted) setAgentIdState(currentId);
          }
        } catch (error) {
          console.warn('SignalForge: Could not initialize backend agent session (backend offline?), using local state:', error);
        }
      }

      if (!currentId) {
        isFetchingRef.current = false;
        return;
      }

      // 2. Load Feed (GET /api/agent/feed?agentId=...)
      try {
        const feedData = await getFeed(currentId);
        if (isMounted && feedData && Array.isArray(feedData.posts)) {
          const adaptedPosts = adaptFeedPosts(feedData.posts);
          setPublishedPosts(adaptedPosts);
        }
      } catch (error) {
        console.warn('SignalForge: Failed to fetch live feed:', error);
      }

      // 3. Load Persona Configuration (GET /api/agent/{agent_id}/persona)
      try {
        const personaRes = await getPersona(currentId);
        if (isMounted && personaRes) {
          setPersonaData(personaRes);
          setStatus((prev) => ({
            ...prev,
            personaName: personaRes.persona_name || prev.personaName,
            role: personaRes.primary_domain ? `${personaRes.primary_domain} Signal Analyst` : prev.role,
            designation: currentId ? currentId.toUpperCase().slice(0, 12) : prev.designation,
            currentObjective: personaRes.persona_description || prev.currentObjective,
          }));
        }
      } catch (error) {
        console.warn('SignalForge: Could not fetch persona configuration:', error);
      }

      // 4. Load Feed Configuration (GET /api/agent/{agent_id}/feed/config)
      try {
        const feedConfigRes = await getFeedConfig(currentId);
        if (isMounted && feedConfigRes) {
          setFeedConfig(feedConfigRes);
        }
      } catch (error) {
        console.warn('SignalForge: Could not fetch feed configuration:', error);
      }

      // 5. Load Workflow History (GET /api/agent/{agent_id}/workflows) & Inspection
      try {
        const wfRes = await getWorkflows(currentId, 10, 0);
        if (isMounted && wfRes && Array.isArray(wfRes.items)) {
          setWorkflowHistory(wfRes.items);
          if (wfRes.items.length > 0) {
            const latestWfId = wfRes.items[0].workflow_id;
            try {
              const insp = await inspectWorkflow(currentId, latestWfId);
              if (isMounted && insp) {
                setLatestInspection(insp);
              }
            } catch {
              // Ignore inspection fetch failures
            }
          }
        }
      } catch (error) {
        console.warn('SignalForge: Could not fetch workflow history:', error);
      } finally {
        isFetchingRef.current = false;
      }
    };

    setupAgentAndLoad();

    const intervalId = setInterval(() => {
      setupAgentAndLoad();
    }, 30000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  // Trigger Real Workflow Execution via POST /api/agent/{agent_id}/workflow/run
  const handleTriggerScan = async () => {
    setIsScanning(true);
    setBanner(null);
    setStatus((prev) => ({ ...prev, state: 'SCANNING' }));

    const currentAgentId = agentId || getStoredAgentId();

    if (!currentAgentId) {
      setBanner({
        type: 'error',
        text: 'Agent session not initialized. Unable to execute workflow.',
      });
      setIsScanning(false);
      setStatus((prev) => ({ ...prev, state: 'IDLE' }));
      return;
    }

    try {
      const wfResult = await runWorkflow(currentAgentId, {
        max_topics: 2,
        editorial_threshold: 0.5,
        enable_dry_run_publication: true,
        publication_mode: 'dry_run',
      });

      const wfId = wfResult.workflow_id;

      // 1. Refresh Live Feed from Backend
      try {
        const updatedFeed = await getFeed(currentAgentId);
        if (updatedFeed && Array.isArray(updatedFeed.posts)) {
          setPublishedPosts(adaptFeedPosts(updatedFeed.posts));
        }
      } catch (feedErr) {
        console.warn('Could not refresh feed after workflow run:', feedErr);
      }

      // 2. Fetch Workflow Inspection & History
      try {
        const insp = await inspectWorkflow(currentAgentId, wfId);
        if (insp) setLatestInspection(insp);
      } catch (inspErr) {
        console.warn('Could not inspect workflow:', inspErr);
      }

      try {
        const wfHist = await getWorkflows(currentAgentId, 10, 0);
        if (wfHist && Array.isArray(wfHist.items)) {
          setWorkflowHistory(wfHist.items);
        }
      } catch (histErr) {
        console.warn('Could not refresh workflow history:', histErr);
      }

      // 3. Process Diagnostics into Rejected Topics Tab
      if (Array.isArray(wfResult.diagnostics) && wfResult.diagnostics.length > 0) {
        const newRejections: RejectedTopic[] = wfResult.diagnostics.map((d, i) => ({
          id: `diag-${wfId}-${i}`,
          topic: d.title || `Topic ${d.topic_id || i + 1}`,
          source: `Stage: ${d.failed_stage || 'Pipeline Stage'}`,
          rejectedAt: new Date().toLocaleTimeString(),
          rejectionReason: d.sanitized_reason || 'Pipeline execution halted at stage.',
          noiseCategory: 'Out of Domain',
          similarityScore: 0,
        }));
        setRejectedTopics((prev) => [...newRejections, ...prev]);
      }

      // 4. Record Activity Timeline Events from Actual Backend Stages
      if (Array.isArray(wfResult.stages)) {
        const stageEvents: ActivityEvent[] = wfResult.stages.map((st, idx) => ({
          id: `act-${wfId}-${idx}`,
          timestamp: st.completed_at ? new Date(st.completed_at).toLocaleTimeString() : new Date().toLocaleTimeString(),
          type: st.stage_name.includes('discovery')
            ? 'INGESTION'
            : st.stage_name.includes('editorial') || st.stage_name.includes('validation')
            ? 'EVALUATION'
            : st.stage_name.includes('publication')
            ? 'PUBLICATION'
            : 'SYNTHESIS',
          title: `Stage '${st.stage_name}': ${st.status}`,
          detail: st.rationale || `Stage executed with status ${st.status}`,
          status: st.is_successful ? 'success' : st.status === 'BLOCKED' ? 'warning' : 'error',
        }));
        setTimeline((prev) => [...stageEvents, ...prev]);
      }

      // 5. Update Governance & Banner State
      if (wfResult.governance && wfResult.governance.allowed === false) {
        setBanner({
          type: 'error',
          text: `Governance Policy Rejection (HTTP 422 / Blocked): ${wfResult.governance.reason || 'Rules violation'}`,
        });
      } else if (wfResult.status === 'SUCCESS' || wfResult.status === 'PARTIAL_SUCCESS') {
        setBanner({
          type: 'success',
          text: `Workflow execution completed (${wfResult.status}). ${wfResult.publication_ids.length} dry-run post(s) published locally.`,
        });
      } else {
        setBanner({
          type: 'warning',
          text: `Workflow run completed with status '${wfResult.status}': ${wfResult.rationale}`,
        });
      }

      setStatus((prev) => ({
        ...prev,
        state: 'IDLE',
        lastCycleAt: new Date().toLocaleTimeString(),
        totalSignalsProcessed24h: prev.totalSignalsProcessed24h + (wfResult.selected_topic_ids?.length || 0),
      }));
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setBanner({
            type: 'warning',
            text: `Rate Limit Exceeded (HTTP 429): Please wait ${err.retryAfterSeconds || 60} seconds before triggering another workflow cycle.`,
            retryAfter: err.retryAfterSeconds,
          });
        } else if (err.status === 422) {
          setBanner({
            type: 'error',
            text: `Governance / Validation Error (HTTP 422): ${err.message}`,
          });
        } else {
          setBanner({
            type: 'error',
            text: `Backend Error (HTTP ${err.status}): ${err.message}`,
          });
        }
      } else {
        const msg = err instanceof Error ? err.message : 'Unknown backend connection error';
        setBanner({
          type: 'error',
          text: `Backend Service Unavailable: ${msg}`,
        });
      }
      setStatus((prev) => ({ ...prev, state: 'IDLE' }));
    } finally {
      setIsScanning(false);
    }
  };

  // Handle Save Persona & Feed Config via Backend APIs
  const handleSavePersona = async (updated: PersonaUpdateRequest) => {
    const currentAgentId = agentId || getStoredAgentId();
    if (!currentAgentId) {
      throw new Error('No active agent session ID found');
    }

    const savedPersona = await updatePersona(currentAgentId, updated);
    setPersonaData(savedPersona);

    if (updated.preferred_categories || updated.min_relevance_threshold !== undefined) {
      await updateFeedConfig(currentAgentId, {
        allowed_categories: updated.preferred_categories,
        min_relevance_score: updated.min_relevance_threshold,
      });
    }

    setStatus((prev) => ({
      ...prev,
      personaName: savedPersona.persona_name || prev.personaName,
      role: savedPersona.primary_domain ? `${savedPersona.primary_domain} Signal Analyst` : prev.role,
      currentObjective: savedPersona.persona_description || prev.currentObjective,
    }));
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
    <div className="min-h-screen bg-slate-950 text-slate-100 scanline-overlay flex flex-col font-sans">
      {/* Top Header */}
      <Header status={status} onTriggerScan={handleTriggerScan} isScanning={isScanning} />

      {/* Dismissible Banner Alert */}
      {banner && (
        <div className="max-w-7xl w-full mx-auto px-4 lg:px-8 pt-4">
          <div
            className={`p-3.5 rounded-xl border font-mono text-xs flex items-start justify-between gap-3 shadow-lg ${
              banner.type === 'success'
                ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-300'
                : banner.type === 'warning'
                ? 'bg-amber-950/90 border-amber-500/50 text-amber-300'
                : banner.type === 'error'
                ? 'bg-rose-950/90 border-rose-500/50 text-rose-300'
                : 'bg-cyan-950/90 border-cyan-500/50 text-cyan-300'
            }`}
          >
            <div className="flex items-start gap-2">
              {banner.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />}
              {banner.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />}
              {banner.type === 'error' && <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />}
              <span>{banner.text}</span>
            </div>
            <button onClick={() => setBanner(null)} className="text-slate-400 hover:text-slate-200">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

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
            <NovaPersonaPanel status={status} onOpenSettings={() => setIsPersonaModalOpen(true)} />

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
                <ActivityTimeline events={timeline.slice(0, 5)} />
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

      {/* Persona Configuration Modal */}
      <PersonaModal
        isOpen={isPersonaModalOpen}
        onClose={() => setIsPersonaModalOpen(false)}
        currentPersona={personaData}
        onSavePersona={handleSavePersona}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-4 text-center text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>SignalForge — Autonomous AI Technology Intelligence Platform</span>
          <span className="text-slate-600">
            {latestInspection
              ? `Stage Stats: ${latestInspection.stage_stats.succeeded_stages}/${latestInspection.stage_stats.total_stages} Succeeded • Mode: ${latestInspection.governance?.execution_mode || 'dry_run'}`
              : 'NOVA Agent Persona v2.4 • Production Ready'}
          </span>
        </div>
      </footer>
    </div>
  );
}
