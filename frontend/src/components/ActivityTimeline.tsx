import React from 'react';
import { Activity, Info, Radio, Send, FilterX } from 'lucide-react';
import type { ActivityEvent } from '../types';

interface ActivityTimelineProps {
  events: ActivityEvent[];
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ events }) => {
  const getEventIcon = (type: ActivityEvent['type']) => {
    switch (type) {
      case 'INGESTION':
        return <Radio className="w-3.5 h-3.5 text-cyan-400" />;
      case 'EVALUATION':
        return <Activity className="w-3.5 h-3.5 text-violet-400" />;
      case 'REJECTION':
        return <FilterX className="w-3.5 h-3.5 text-amber-400" />;
      case 'PUBLICATION':
        return <Send className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <Info className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const getStatusDot = (status: ActivityEvent['status']) => {
    switch (status) {
      case 'success':
        return 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
      case 'warning':
        return 'bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.5)]';
      case 'error':
        return 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]';
      default:
        return 'bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.5)]';
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-4">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
          AUTONOMOUS ACTIVITY TIMELINE LOG
        </h2>
        <span className="text-xs font-mono text-slate-400">Live Agent Audit Stream</span>
      </div>

      {/* Timeline Stream */}
      {events.length === 0 ? (
        <div className="text-center py-6 text-slate-500 text-xs font-mono">
          No activity log events recorded yet.
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800 font-mono">
          {events.map((evt) => (
          <div key={evt.id} className="relative group">
            
            {/* Pulsating Event Node */}
            <div className={`absolute -left-6 top-1.5 w-2.5 h-2.5 rounded-full ${getStatusDot(evt.status)}`} />

            <div className="bg-slate-950/80 border border-slate-800/80 group-hover:border-cyan-500/30 rounded-xl p-3.5 transition-all">
              <div className="flex items-center justify-between gap-2 text-xs mb-1">
                <div className="flex items-center gap-2">
                  {getEventIcon(evt.type)}
                  <span className="font-bold text-slate-200">{evt.title}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-cyan-300 border border-slate-800">
                    {evt.type}
                  </span>
                </div>
                <span className="text-slate-500 text-[11px]">{evt.timestamp}</span>
              </div>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">{evt.detail}</p>
            </div>

          </div>
        ))}
      </div>
      )}

    </div>
  );
};
