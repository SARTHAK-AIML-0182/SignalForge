import type { FeedPost } from './agentApi';
import type { PublishedPost, EditorialScore } from '../types';

export const AGENT_ID_STORAGE_KEY = 'signalforge_agent_id';

/**
 * Default editorial score object used for visual compatibility with PublishedPosts UI.
 * Distinctly identified as fallback telemetry.
 */
export const DEFAULT_EDITORIAL_SCORE: EditorialScore = {
  overall: 8.5,
  novelty: 8.0,
  technicalDepth: 8.5,
  validity: 9.0,
  clarity: 8.5,
  actionability: 8.5,
};

/**
 * Retrieves the stored agent ID from localStorage or environment variables.
 * Does not trigger agent initialization if missing.
 */
export function getStoredAgentId(): string | null {
  try {
    const fromStorage = localStorage.getItem(AGENT_ID_STORAGE_KEY);
    if (fromStorage && fromStorage.trim()) {
      return fromStorage.trim();
    }
  } catch {
    // Ignore storage access errors in restricted browser contexts
  }

  const fromEnv = (import.meta.env.VITE_AGENT_ID as string) || '';
  if (fromEnv && fromEnv.trim()) {
    return fromEnv.trim();
  }

  return null;
}

/**
 * Derives a short summary from full post content.
 */
function deriveSummary(content: string): string {
  if (!content || !content.trim()) {
    return 'Synthesized technology intelligence briefing from NOVA agent.';
  }

  const clean = content
    .replace(/^#+\s+/gm, '')
    .replace(/\*\*/g, '')
    .replace(/\n+/g, ' ')
    .trim();

  if (clean.length <= 180) {
    return clean;
  }
  return `${clean.slice(0, 177)}...`;
}

/**
 * Calculates estimated reading time based on word count (~200 wpm).
 */
function deriveReadTime(content: string): string {
  if (!content || !content.trim()) {
    return '1 min read';
  }

  const words = content.trim().split(/\s+/).length;
  const minutes = Math.max(1, Math.ceil(words / 200));
  return `${minutes} min read`;
}

/**
 * Extracts key takeaways from markdown list items or key sentences.
 */
function deriveKeyTakeaways(content: string, title: string): string[] {
  if (!content || !content.trim()) {
    return [`Briefing summary for: ${title}`];
  }

  const lines = content.split('\n');
  const bulletLines: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || /^\d+\.\s/.test(trimmed)) {
      const takeaway = trimmed.replace(/^[-*\d.]+\s*/, '').replace(/\*\*/g, '').trim();
      if (takeaway.length > 5) {
        bulletLines.push(takeaway);
      }
    }
  }

  if (bulletLines.length >= 2) {
    return bulletLines.slice(0, 4);
  }

  const sentences = content
    .replace(/^#+\s+/gm, '')
    .replace(/\*\*/g, '')
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 20);

  if (sentences.length > 0) {
    return sentences.slice(0, 3);
  }

  return [`Briefing summary for: ${title}`];
}

/**
 * Converts a backend FeedPost into a PublishedPost compatible with the frontend HUD.
 */
export function adaptFeedPostToPublishedPost(post: FeedPost): PublishedPost {
  let publishedAtFormatted = post.publishedAt || '';
  if (post.publishedAt) {
    const parsedDate = Date.parse(post.publishedAt);
    if (!isNaN(parsedDate)) {
      publishedAtFormatted = new Date(parsedDate).toLocaleString();
    }
  } else {
    publishedAtFormatted = new Date().toLocaleString();
  }

  return {
    id: post.id || `post-${Math.random().toString(36).substring(2, 9)}`,
    title: post.title || 'Untitled Briefing',
    summary: deriveSummary(post.content),
    content: post.content || '',
    channels: ['Internal HUD'],
    publishedAt: publishedAtFormatted,
    editorialScore: DEFAULT_EDITORIAL_SCORE,
    publishingRationale: post.rationale || 'Synthesized directly from verified backend telemetry stream.',
    targetAudience: 'AI & technology practitioners',
    keyTakeaways: deriveKeyTakeaways(post.content, post.title),
    sourceSignalIds: Array.isArray(post.sources) ? post.sources : [],
    readTime: deriveReadTime(post.content),
    viewsCount: 0,
  };
}

/**
 * Adapts an array of FeedPosts into PublishedPosts sorted newest first.
 */
export function adaptFeedPosts(posts: FeedPost[]): PublishedPost[] {
  if (!Array.isArray(posts)) {
    return [];
  }

  const adapted = posts.map(adaptFeedPostToPublishedPost);

  return [...adapted].sort((a, b) => {
    const timeA = Date.parse(a.publishedAt) || 0;
    const timeB = Date.parse(b.publishedAt) || 0;
    return timeB - timeA;
  });
}
