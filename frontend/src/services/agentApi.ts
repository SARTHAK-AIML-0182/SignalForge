/**
 * SignalForge Agent API Service
 * Integration layer for FastAPI backend endpoints.
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

export interface Persona {
  name: string;
  domain: string;
}

export interface AgentInitRequest {
  persona: Persona;
}

export type AgentInitResponse = Record<string, unknown>;

export interface FeedPost {
  id: string;
  title: string;
  content: string;
  publishedAt: string;
  sources: string[];
  rationale: string;
}

export interface FeedResponse {
  agentId: string;
  posts: FeedPost[];
  status: string;
  timestamp: string;
}

export interface WorkflowItem {
  workflow_id: string;
  agent_id: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  is_successful: boolean;
  rationale: string;
  selected_topic_count: number;
  selected_topic_ids_count: number;
  research_count: number;
  draft_count: number;
  publication_count: number;
  publication_ids_count: number;
}

export interface WorkflowsResponse {
  items: WorkflowItem[];
  total: number;
  limit: number;
  offset: number;
}

export type WorkflowStatusResponse = Record<string, unknown>;

export type WorkflowInspectionResponse = Record<string, unknown>;

/**
 * Internal helper to validate HTTP response status and extract JSON payload.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
    try {
      const errorData = (await response.json()) as Record<string, unknown>;
      if (errorData && typeof errorData === 'object') {
        const detail = errorData.detail || errorData.message;
        if (typeof detail === 'string') {
          errorMessage = detail;
        }
      }
    } catch {
      // Ignore JSON parse errors for non-JSON error responses
    }
    throw new Error(errorMessage);
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
    headers: {
      'Content-Type': 'application/json',
    },
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
    headers: {
      'Accept': 'application/json',
    },
  });
  return handleResponse<FeedResponse>(response);
}

/**
 * 3. List workflows
 * GET /api/agent/{agent_id}/workflows
 */
export async function getWorkflows(agentId: string): Promise<WorkflowsResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/workflows`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });
  return handleResponse<WorkflowsResponse>(response);
}

/**
 * 4. Get workflow status
 * GET /api/agent/{agent_id}/workflow/{workflow_id}
 */
export async function getWorkflow(agentId: string, workflowId: string): Promise<WorkflowStatusResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/workflow/${encodeURIComponent(workflowId)}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });
  return handleResponse<WorkflowStatusResponse>(response);
}

/**
 * 5. Inspect workflow
 * GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection
 */
export async function inspectWorkflow(agentId: string, workflowId: string): Promise<WorkflowInspectionResponse> {
  const url = `${API_BASE_URL}/api/agent/${encodeURIComponent(agentId)}/workflow/${encodeURIComponent(workflowId)}/inspection`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });
  return handleResponse<WorkflowInspectionResponse>(response);
}
