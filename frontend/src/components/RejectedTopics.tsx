import React, { useState } from 'react';
import { FilterX, AlertTriangle, Search } from 'lucide-react';
import type { RejectedTopic } from '../types';

interface RejectedTopicsProps {
  rejectedTopics: RejectedTopic[];
}

export const RejectedTopics: React.FC<RejectedTopicsProps> = ({ rejectedTopics }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const categories = ['ALL', 'Low Novelty', 'Unverified Speculation', 'Marketing Hype', 'Duplicate'];

  const filtered = rejectedTopics.filter((item) => {
    const matchesCat = selectedCategory === 'ALL' || item.noiseCategory === selectedCategory;
    const matchesQuery =
      item.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.rejectionReason.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.source.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesQuery;
  });

  const getBadgeColor = (category: string) => {
    switch (category) {
      case 'Duplicate':
        return 'bg-violet-950 text-violet-400 border-violet-800';
      case 'Low Novelty':
        return 'bg-amber-950 text-amber-400 border-amber-800';
      case 'Marketing Hype':
        return 'bg-pink-950 text-pink-400 border-pink-800';
      case 'Unverified Speculation':
        return 'bg-rose-950 text-rose-400 border-rose-800';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-4">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
            <FilterX className="w-4 h-4 text-amber-400" />
            REJECTED TOPICS & NOISE AUDIT LOG
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Topics flagged and rejected by NOVA's autonomous novelty & verification engine.
          </p>
        </div>

        {/* Search & Category Filter */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search rejections..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono w-44 sm:w-56"
            />
          </div>

          <div className="flex flex-wrap gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 font-mono text-xs">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  selectedCategory === cat
                    ? 'bg-amber-950 text-amber-300 font-semibold border border-amber-800'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Rejections List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs font-mono">
            No rejected topics match current filter.
          </div>
        ) : (
          filtered.map((item) => (
            <div
              key={item.id}
              className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 transition-all hover:border-amber-500/30"
            >
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                    <span className={`px-2 py-0.5 rounded border text-[11px] font-semibold ${getBadgeColor(item.noiseCategory)}`}>
                      {item.noiseCategory}
                    </span>
                    <span className="text-slate-400">{item.rejectedAt}</span>
                    <span className="text-slate-500">• {item.source}</span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-200">
                    {item.topic}
                  </h3>

                  <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800/80 text-xs text-amber-300/90 font-mono flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                    <span>{item.rejectionReason}</span>
                  </div>
                </div>

                {/* Similarity Metric */}
                <div className="flex md:flex-col items-center md:items-end justify-between border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-4 min-w-[130px] font-mono text-xs">
                  <span className="text-[10px] text-slate-500 uppercase">REDUNDANCY SCORE</span>
                  <span className="text-sm font-bold text-amber-400">{item.similarityScore}% Match</span>
                  <span className="text-[10px] text-slate-500 mt-1">Filtered in Loop</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
};
