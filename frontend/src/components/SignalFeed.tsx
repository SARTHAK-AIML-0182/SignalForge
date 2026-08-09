import React, { useState } from 'react';
import { Search, Radio, ArrowUpRight } from 'lucide-react';
import type { Signal } from '../types';

interface SignalFeedProps {
  signals: Signal[];
  onSelectSignal: (signal: Signal) => void;
}

export const SignalFeed: React.FC<SignalFeedProps> = ({ signals, onSelectSignal }) => {
  const [selectedSource, setSelectedSource] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const sources = ['ALL', 'arXiv', 'GitHub', 'HackerNews', 'TechCrunch'];

  const filteredSignals = signals.filter((sig) => {
    const matchesSource = selectedSource === 'ALL' || sig.sourceType === selectedSource;
    const matchesQuery =
      sig.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sig.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sig.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSource && matchesQuery;
  });

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
            <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
            DISCOVERED SIGNALS TELEMETRY
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time tech signal streams evaluated by NOVA neural scoring mesh.
          </p>
        </div>

        {/* Search & Source Filter */}
        <div className="flex flex-wrap items-center gap-3">
          
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Filter signals or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono w-48 sm:w-60"
            />
          </div>

          {/* Source Tabs */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 font-mono text-xs">
            {sources.map((src) => (
              <button
                key={src}
                onClick={() => setSelectedSource(src)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  selectedSource === src
                    ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {src}
              </button>
            ))}
          </div>

        </div>
      </div>

      {/* Signal List */}
      <div className="mt-4 space-y-3">
        {filteredSignals.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs font-mono">
            No signals found matching criteria.
          </div>
        ) : (
          filteredSignals.map((sig) => (
            <div
              key={sig.id}
              onClick={() => onSelectSignal(sig)}
              className="group bg-slate-950/70 hover:bg-slate-900 border border-slate-800/80 hover:border-cyan-500/40 rounded-xl p-4 transition-all duration-200 cursor-pointer relative overflow-hidden"
            >
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                
                {/* Main Content */}
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-cyan-400 border border-slate-700">
                      {sig.sourceType}
                    </span>
                    <span className="text-xs font-mono text-slate-500">{sig.discoveredAt}</span>
                    <span className="text-xs font-mono text-slate-400">• {sig.source}</span>
                  </div>

                  <h3 className="text-sm font-semibold text-slate-100 group-hover:text-cyan-300 transition-colors leading-snug">
                    {sig.title}
                  </h3>

                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                    {sig.summary}
                  </p>

                  <div className="flex flex-wrap items-center gap-2 pt-2">
                    {sig.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-slate-300 border border-slate-800"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Metrics Sidebar inside Card */}
                <div className="flex md:flex-col items-center md:items-end justify-between border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-4 min-w-[140px] font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">VELOCITY SCORE</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <div className="w-16 bg-slate-900 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full rounded-full"
                          style={{ width: `${sig.velocityScore}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-cyan-300">{sig.velocityScore}</span>
                    </div>
                  </div>

                  <div className="mt-2 text-right">
                    <span className="text-[10px] text-slate-500 block">RELEVANCE</span>
                    <span className="text-xs font-bold text-emerald-400">{sig.relevanceScore} / 10</span>
                  </div>

                  <button className="mt-2 text-[11px] text-cyan-400 group-hover:underline flex items-center gap-1">
                    <span>Inspect</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </button>
                </div>

              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
};
