import React from 'react';
import { CheckCircle2, RefreshCcw, AlertTriangle, Network } from 'lucide-react';
import type { DataSource } from '../types';

interface SourcesGridProps {
  sources: DataSource[];
}

export const SourcesGrid: React.FC<SourcesGridProps> = ({ sources }) => {
  const getStatusBadge = (status: DataSource['status']) => {
    switch (status) {
      case 'HEALTHY':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" /> HEALTHY
          </span>
        );
      case 'SYNCING':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
            <RefreshCcw className="w-3 h-3 text-cyan-400 animate-spin" /> SYNCING
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
            <AlertTriangle className="w-3 h-3 text-amber-400" /> DEGRADED
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-4">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
            <Network className="w-4 h-4 text-cyan-400" />
            TELEMETRY INGESTION MESH SOURCES
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Active data providers monitored by SignalForge ingestion pipeline.
          </p>
        </div>
        <span className="text-xs font-mono text-cyan-300 px-2.5 py-1 rounded bg-slate-950 border border-slate-800">
          5 / 5 Operational Streams
        </span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sources.map((src) => (
          <div
            key={src.id}
            className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 transition-all hover:border-cyan-500/40 relative overflow-hidden"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-500 uppercase">{src.type}</span>
                <h3 className="text-sm font-bold text-slate-100 font-mono">{src.name}</h3>
              </div>
              {getStatusBadge(src.status)}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-900 grid grid-cols-2 gap-2 text-xs font-mono">
              <div>
                <span className="text-slate-500 text-[10px] block">RELIABILITY INDEX</span>
                <span className="text-cyan-400 font-bold">{src.reliabilityScore}%</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">AVG LATENCY</span>
                <span className="text-slate-300 font-bold">{src.avgLatency}</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">24H SIGNALS</span>
                <span className="text-emerald-400 font-bold">{src.signalCount24h}</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">LAST SYNCED</span>
                <span className="text-slate-400">{src.lastSync}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
