import React from 'react';
import { X, ExternalLink, Activity, Tag } from 'lucide-react';
import type { Signal } from '../types';

interface SignalModalProps {
  signal: Signal | null;
  onClose: () => void;
}

export const SignalModal: React.FC<SignalModalProps> = ({ signal, onClose }) => {
  if (!signal) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-cyan-500/40 rounded-xl max-w-2xl w-full p-6 relative shadow-[0_0_40px_rgba(6,182,212,0.2)] max-h-[90vh] overflow-y-auto">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 p-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Badge */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
            {signal.sourceType} Telemetry Signal
          </span>
          <span className="text-xs font-mono text-slate-400">Discovered {signal.discoveredAt}</span>
        </div>

        {/* Title */}
        <h2 className="text-lg font-bold text-slate-100 leading-snug">{signal.title}</h2>

        {/* Source & External Link */}
        <div className="mt-2 flex items-center gap-2 text-xs font-mono text-cyan-400">
          <span>Source: {signal.source}</span>
          <a
            href={signal.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 hover:underline text-cyan-300"
          >
            <span>Open Link</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Summary */}
        <div className="mt-4 p-4 bg-slate-950/80 border border-slate-800 rounded-lg">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">Signal Abstract & Synthesis</h3>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">{signal.summary}</p>
        </div>

        {/* Telemetry Metrics */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-xs">
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 block text-[10px]">VELOCITY SCORE</span>
            <span className="text-cyan-400 font-bold text-base">{signal.velocityScore} / 100</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 block text-[10px]">RELEVANCE INDEX</span>
            <span className="text-emerald-400 font-bold text-base">{signal.relevanceScore} / 10</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 block text-[10px]">SENTIMENT POLARITY</span>
            <span className={`font-bold text-base capitalize ${
              signal.sentiment === 'bullish' ? 'text-emerald-400' : 'text-amber-400'
            }`}>
              {signal.sentiment}
            </span>
          </div>
        </div>

        {/* Tags */}
        <div className="mt-4 flex flex-wrap items-center gap-1.5">
          {signal.tags.map((tag, idx) => (
            <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
              <Tag className="w-3 h-3 text-cyan-400" />
              {tag}
            </span>
          ))}
        </div>

        {/* Raw Telemetry JSON */}
        <div className="mt-4 pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" /> RAW TELEMETRY PAYLOAD
            </span>
          </div>
          <pre className="bg-slate-950 p-3 rounded-lg text-[11px] font-mono text-cyan-300 border border-slate-800/80 overflow-x-auto">
            {JSON.stringify(signal.rawTelemetry, null, 2)}
          </pre>
        </div>

      </div>
    </div>
  );
};
