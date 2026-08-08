import React, { useState } from 'react';
import { Send, Award, Sparkles, ChevronDown, ChevronUp, CheckCircle2, Clock, Eye } from 'lucide-react';
import type { PublishedPost } from '../types';

interface PublishedPostsProps {
  posts: PublishedPost[];
}

export const PublishedPosts: React.FC<PublishedPostsProps> = ({ posts }) => {
  const [expandedPostId, setExpandedPostId] = useState<string | null>(posts[0]?.id || null);

  const toggleExpand = (id: string) => {
    setExpandedPostId(expandedPostId === id ? null : id);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-4">
      
      {/* Section Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
            <Send className="w-4 h-4 text-emerald-400" />
            PUBLISHED INTELLIGENCE BRIEFINGS
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Verified technology briefings synthesized by NOVA with AI publishing rationale.
          </p>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
          {posts.length} Briefings Broadcasted
        </span>
      </div>

      {/* Briefings List */}
      <div className="space-y-4">
        {posts.map((post) => {
          const isExpanded = expandedPostId === post.id;
          const scores = post.editorialScore;

          return (
            <div
              key={post.id}
              className={`border rounded-xl transition-all overflow-hidden ${
                isExpanded
                  ? 'bg-slate-950 border-cyan-500/40 shadow-[0_0_25px_rgba(6,182,212,0.1)]'
                  : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              {/* Briefing Header Bar */}
              <div
                onClick={() => toggleExpand(post.id)}
                className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer select-none"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      Briefing #{post.id}
                    </span>
                    <span className="text-slate-400">{post.publishedAt}</span>
                    <span className="text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {post.readTime}
                    </span>
                    <span className="text-slate-500 flex items-center gap-1">
                      <Eye className="w-3 h-3" /> {post.viewsCount} reads
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-100 group-hover:text-cyan-300">
                    {post.title}
                  </h3>

                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                    {post.summary}
                  </p>
                </div>

                {/* Overall Score Badge */}
                <div className="flex items-center gap-4 min-w-[170px] justify-between md:justify-end">
                  <div className="text-right font-mono">
                    <span className="text-[10px] text-slate-500 uppercase block">EDITORIAL SCORE</span>
                    <span className="text-lg font-bold text-emerald-400">{scores.overall} / 10</span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-900 text-slate-400">
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </div>
                </div>
              </div>

              {/* Expanded Detail Panel */}
              {isExpanded && (
                <div className="p-5 border-t border-slate-800/80 bg-slate-950/90 space-y-6 font-sans">
                  
                  {/* Channels & Target Audience */}
                  <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400">Broadcast Channels:</span>
                      <div className="flex items-center gap-1.5">
                        {post.channels.map((ch, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                            {ch}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400">Target Audience: </span>
                      <span className="text-slate-200">{post.targetAudience}</span>
                    </div>
                  </div>

                  {/* AI Publishing Rationale */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-cyan-950/40 border border-cyan-500/30">
                    <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-semibold mb-2">
                      <Sparkles className="w-4 h-4 text-cyan-400" />
                      NOVA PUBLISHING RATIONALE
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      "{post.publishingRationale}"
                    </p>
                  </div>

                  {/* Editorial Score Radar Breakdown */}
                  <div>
                    <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <Award className="w-4 h-4 text-violet-400" /> EDITORIAL QUALITY EVALUATION BREAKDOWN
                    </h4>
                    
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 text-[10px] block">NOVELTY</span>
                        <span className="text-cyan-400 font-bold text-base">{scores.novelty} / 10</span>
                        <div className="w-full bg-slate-950 h-1 rounded-full mt-1.5 overflow-hidden">
                          <div className="bg-cyan-400 h-full" style={{ width: `${scores.novelty * 10}%` }} />
                        </div>
                      </div>

                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 text-[10px] block">TECH DEPTH</span>
                        <span className="text-emerald-400 font-bold text-base">{scores.technicalDepth} / 10</span>
                        <div className="w-full bg-slate-950 h-1 rounded-full mt-1.5 overflow-hidden">
                          <div className="bg-emerald-400 h-full" style={{ width: `${scores.technicalDepth * 10}%` }} />
                        </div>
                      </div>

                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 text-[10px] block">VALIDITY</span>
                        <span className="text-violet-400 font-bold text-base">{scores.validity} / 10</span>
                        <div className="w-full bg-slate-950 h-1 rounded-full mt-1.5 overflow-hidden">
                          <div className="bg-violet-400 h-full" style={{ width: `${scores.validity * 10}%` }} />
                        </div>
                      </div>

                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 text-[10px] block">CLARITY</span>
                        <span className="text-amber-400 font-bold text-base">{scores.clarity} / 10</span>
                        <div className="w-full bg-slate-950 h-1 rounded-full mt-1.5 overflow-hidden">
                          <div className="bg-amber-400 h-full" style={{ width: `${scores.clarity * 10}%` }} />
                        </div>
                      </div>

                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 col-span-2 sm:col-span-1">
                        <span className="text-slate-400 text-[10px] block">ACTIONABILITY</span>
                        <span className="text-cyan-300 font-bold text-base">{scores.actionability} / 10</span>
                        <div className="w-full bg-slate-950 h-1 rounded-full mt-1.5 overflow-hidden">
                          <div className="bg-cyan-300 h-full" style={{ width: `${scores.actionability * 10}%` }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Key Takeaways */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider">Key Strategic Takeaways</h4>
                    <ul className="space-y-1.5 text-xs text-slate-300">
                      {post.keyTakeaways.map((takeaway, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <span>{takeaway}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Full Briefing Text Preview */}
                  <div className="p-4 bg-slate-900/70 border border-slate-800 rounded-lg text-xs text-slate-300 font-mono whitespace-pre-line leading-relaxed max-h-60 overflow-y-auto">
                    {post.content}
                  </div>

                </div>
              )}
            </div>
          );
        })}
      </div>

    </div>
  );
};
