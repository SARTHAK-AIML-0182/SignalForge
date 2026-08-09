/**
 * SignalForge Agent API Service
 * Centralized integration layer for FastAPI backend endpoints.
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  retryAfterSeconds?: number;
  detail?: string;

  constructor(message: string, status: number, retryAfterSeconds?: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
    this.detail = detail;
  }
}

export interface Persona {
  name: string;
  domain: string;
}

export interface AgentInitRequest {
  persona: Persona;
}

export interface AgentInitResponse {
  agentId: string;
}

export interface FeedItem {
  id: string;
  title: string;
  content: string;
  publishedAt: string;
  sources: string[];
  rationale?: string | null;
}

export type FeedPost = FeedItem;

export interface FeedResponse {
  agentId: string;
  posts: FeedItem[];
  status: string;
  timestamp: string;
}

export interface WorkflowStageResponse {
  stage_name: string;
  status: string;
  started_at: string;
  completed_at: string;
  is_successful: boolean;
  rationale: string;
  entity_ids?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface WorkflowPolicy {
  max_topics: number;
  editorial_threshold: number;
  enable_dry_run_publication: boolean;
  publication_mode: string;
  max_topics_upper_bound?: number;
  validation_threshold?: number;
  max_research_items?: number;
}

export interface WorkflowGovernanceDecision {
  allowed: boolean;
  execution_mode: string;
  publication_allowed: boolean;
  reason: string;
  blocked_rules: string[];
  warnings: string[];
  policy?: WorkflowPolicy | Record<string, unknown>;
}

export interface TopicFailureDiagnostic {
  topic_id: string;
  title: string;
  failed_stage: string;
  sanitized_reason: string;
  stage_status: string;
  research_id?: string | null;
  draft_id?: string | null;
  publication_id?: string | null;
  is_publishable: boolean;
}

export interface TraceabilitySummary {
  discovered_topic_count: number;
  selected_topic_count: number;
  researched_count: number;
  validated_count: number;
  synthesized_count: number;
  brief_count: number;
  draft_count: number;
  publishable_count: number;
  published_count: number;
  failure_count: number;
}

export interface WorkflowRunRequest {
  max_topics?: number;
  editorial_threshold?: number;
  enable_dry_run_publication?: boolean;
  publication_mode?: 'dry_run' | 'disabled';
}

export interface WorkflowRunResponse {
  workflow_id: string;
  agent_id: string;
  status: string;
  started_at: string;
  completed_at: string;
  is_successful: boolean;
  halted_at_stage?: string | null;
  rationale: string;
  selected_topic_ids: string[];
  research_ids: string[];
  draft_ids: string[];
  publication_ids: string[];
  stages: WorkflowStageResponse[];
  traceability: Record<string, unknown>;
  policy?: WorkflowPolicy | null;
  governance?: WorkflowGovernanceDecision | null;
  diagnostics: TopicFailureDiagnostic[];
}

export interface WorkflowSummaryResponse {
  workflow_id: string;
  agent_id: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration_seconds?: number | null;
  is_successful: boolean;
  rationale: string;
  selected_topic_count: number;
  selected_topic_ids_count: number;
  research_count: number;
  draft_count: number;
  publication_count: number;
  publication_ids_count: number;
  policy?: WorkflowPolicy | null;
  governance?: WorkflowGovernanceDecision | null;
  diagnostics: TopicFailureDiagnostic[];
}

export interface WorkflowsResponse {
  items: WorkflowSummaryResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface WorkflowStageStats {
  total_stages: number;
  succeeded_stages: number;
  failed_stages: number;
  blocked_stages: number;
  skipped_stages: number;
  running_stages: number;
}

export interface WorkflowInspectionResponse {
  workflow_id: string;
  agent_id: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration_seconds?: number | null;
  is_successful: boolean;
  halted_at_stage?: string | null;
  rationale: string;
  stage_stats: WorkflowStageStats;
  selected_topic_count: number;
  research_count: number;
  draft_count: number;
  publication_count: number;
  traceability_summary: TraceabilitySummary | Record<string, unknown>;
  policy?: WorkflowPolicy | null;
  governance?: WorkflowGovernanceDecision | null;
  diagnostics: TopicFailureDiagnostic[];
}

export interface PersonaResponse {
  agent_id: string;
  persona_name: string;
  persona_description?: string | null;
  primary_domain: string;
  secondary_domains: string[];
  preferred_categories: string[];
  excluded_categories: string[];
  preferred_keywords: string[];
  excluded_keywords: string[];
  audience_description?: string | null;
  style_tone?: string | null;
  min_relevance_threshold: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PersonaUpdateRequest {
  persona_name: string;
  primary_domain: string;
  persona_description?: string;
  secondary_domains?: string[];
  preferred_categories?: string[];
  excluded_categories?: string[];
  preferred_keywords?: string[];
  excluded_keywords?: string[];
  audience_description?: string;
  style_tone?: string;
  min_relevance_threshold?: number;
}

export interface FeedConfigResponse {
  agent_id: string;
  max_topics: number;
  min_relevance_score: number;
  allowed_categories: string[];
  excluded_categories: string[];
  preferred_keywords: string[];
  excluded_keywords: string[];
}

export interface FeedConfigUpdateRequest {
  max_topics?: number;
  min_relevance_score?: number;
  allowed_categories?: string[];
  excluded_categories?: string[];
  preferred_keywords?: string[];
  excluded_keywords?: string[];
}

/**
 * Internal helper to validate HTTP response status, extract JSON payload, and parse errors cleanly.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
    let detailMessage: string | undefined;

    // Extract Retry-After header for rate-limited (429) responses
    let retryAfterSeconds: number | undefined;
    const retryHeader = response.headers.get('Retry-After');
    if (retryHeader) {
      const parsedRetry = parseInt(retryHeader, 10);
      if (!isNaN(parsedRetry)) {
        retryAfterSeconds = parsedRetry;
      }
    }

    try {
      const errorData = (await response.json()) as Record<string, unknown>;
      if (errorData && typeof errorData === 'object') {
        const detail = errorData.detail || errorData.message;
        if (typeof detail === 'string') {
          detailMessage = detail;
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          // Format FastAPI Pydantic validation error array
          const messages = detail.map((d) => (typeof d === 'object' && d && 'msg' in d ? String(d.msg) : JSON.stringify(d)));
          detailMessage = messages.join('; ');
          errorMessage = detailMessage;
        }
      }
    } catch {
      // Ignore JSON parse errors for non-JSON error responses
    }

    throw new ApiError(errorMessage, response.status, retryAfterSeconds, detailMessage);
  }
  return response.json() as Promise<T>;
}

/**
 * 1. Initialize agent
 * POST /api/agent/init
 */
export async function initializeAgent(
  payload: AgentInitRequest = { persona: { name: 'NOVA', domain: 'AI & Emerging Technology' } }
): Promise<AgentInitResponse> {
  const url = `${API_BASE_URL}/api/agent/init`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<AgentInitResponse>(response);
}

/**
 * 2. Get feed
 * GET /api/agent/feed?agentId={agentId}
 */
export async function getFeed(agentId: string): Promise<FeedResponse> {
  const url = `${API_BASE_URL}/api/agent/feed?agentId=${encodeURIComponent(agentId)}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  return handleResponse<FeedResponse>(response);
}

/**
 * 3. Run workflow
 * POST /api/agent/{agent_id}/workflow/run
 */
export async function runWorkflow(
  agentId: string,
  payload: WorkflowRunRequest = { max_topics: 2, editorial_threshold: 0.5, enable_dry_run_publication: true, publication_mode: 'dry_run' }
): Promise<WorkflowRunResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/workflow/run`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<WorkflowRunResponse>(response);
}

/**
 * 4. Get workflow status
 * GET /api/agent/{agent_id}/workflow/{workflow_id}
 */
export async function getWorkflowStatus(agentId: string, workflowId: string): Promise<WorkflowRunResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/workflow/${encodeURIComponent(workflowId)}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  return handleResponse<WorkflowRunResponse>(response);
}

/**
 * 5. Inspect workflow
 * GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection
 */
export async function inspectWorkflow(agentId: string, workflowId: string): Promise<WorkflowInspectionResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/workflow/${encodeURIComponent(workflowId)}/inspection`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  return handleResponse<WorkflowInspectionResponse>(response);
}

/**
 * 6. List workflows
 * GET /api/agent/{agent_id}/workflows
 */
export async function getWorkflows(
  agentId: string,
  limit: number = 20,
  offset: number = 0,
  status?: string,
  successful?: boolean
): Promise<WorkflowsResponse> {
  const params = new URLSearchParams();
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  if (status) params.set('status', status);
  if (successful !== undefined) params.set('successful', String(successful));

  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/workflows?${params.toString()}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  return handleResponse<WorkflowsResponse>(response);
}

/**
 * 7. Get persona
 * GET /api/agent/{agent_id}/persona
 */
export async function getPersona(agentId: string): Promise<PersonaResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/persona`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  return handleResponse<PersonaResponse>(response);
}

/**
 * 8. Update persona
 * PUT /api/agent/{agent_id}/persona
 */
export async function updatePersona(agentId: string, payload: PersonaUpdateRequest): Promise<PersonaResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/persona`;
  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<PersonaResponse>(response);
}

/**
 * 9. Get feed config
 * GET /api/agent/{agent_id}/feed/config
 */
export async function getFeedConfig(agentId: string): Promise<FeedConfigResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/feed/config`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  return handleResponse<FeedConfigResponse>(response);
}

/**
 * 10. Update feed config
 * PUT /api/agent/{agent_id}/feed/config
 */
export async function updateFeedConfig(agentId: string, payload: FeedConfigUpdateRequest): Promise<FeedConfigResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/feed/config`;
  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<FeedConfigResponse>(response);
}
