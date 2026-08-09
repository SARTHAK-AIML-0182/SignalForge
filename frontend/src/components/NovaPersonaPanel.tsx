import React from 'react';
import { Bot, Cpu, Sparkles, Gauge, CheckCircle2, Target, Settings } from 'lucide-react';
import type { NovaAgentStatus } from '../types';

interface NovaPersonaPanelProps {
  status: NovaAgentStatus;
  onOpenSettings?: () => void;
}

export const NovaPersonaPanel: React.FC<NovaPersonaPanelProps> = ({ status, onOpenSettings }) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 relative overflow-hidden backdrop-blur-sm shadow-xl">
      {/* Decorative Glow Background */}
      <div className="absolute -right-16 -top-16 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -left-16 -bottom-16 w-48 h-48 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        
        {/* NOVA Identity & Bio */}
        <div className="lg:col-span-5 flex items-start gap-4">
          <div className="relative flex-shrink-0">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-950 to-slate-900 border border-cyan-500/50 flex items-center justify-center text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.3)]">
              <Bot className="w-8 h-8" />
            </div>
            <div className="absolute -bottom-1 -right-1 p-1 bg-emerald-950 rounded-full border border-emerald-500 text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100 font-mono tracking-tight">{status.personaName}</h2>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800">
                Designation: {status.designation}
              </span>
              {onOpenSettings && (
                <button
                  onClick={onOpenSettings}
                  className="p-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 border border-slate-700 transition flex items-center gap-1 text-[11px] font-mono ml-auto"
                  title="Configure Agent Persona & Feed Rules"
                >
                  <Settings className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Config</span>
                </button>
              )}
            </div>
            <p className="text-xs text-cyan-400 font-medium mt-0.5">{status.role}</p>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Autonomous AI agent scanning global arXiv papers, code repos, and technical forums to distill high-confidence technology signals and publish editorial briefings.
            </p>
          </div>
        </div>

        {/* Current Objective HUD */}
        <div className="lg:col-span-4 bg-slate-950/80 border border-slate-800/80 rounded-lg p-3.5 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2 border-b border-slate-800 pb-1.5">
            <span className="flex items-center gap-1.5 text-cyan-400 font-medium">
              <Target className="w-3.5 h-3.5 text-cyan-400" />
              CURRENT OBJECTIVE
            </span>
            <span className="text-[10px] text-slate-500">AUTONOMOUS LOOP</span>
          </div>
          <p className="text-slate-200 text-xs leading-relaxed font-sans">
            "{status.currentObjective}"
          </p>
          <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
            <span>Processed 24h: <strong className="text-cyan-300 font-mono">{status.totalSignalsProcessed24h} signals</strong></span>
            <span>Neural Confidence: <strong className="text-emerald-400 font-mono">{status.confidenceScore}%</strong></span>
          </div>
        </div>

        {/* System Load & Active Models */}
        <div className="lg:col-span-3 space-y-3 font-mono text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
          <div>
            <div className="flex justify-between text-slate-400 mb-1 text-[11px]">
              <span className="flex items-center gap-1">
                <Cpu className="w-3 h-3 text-cyan-400" /> CPU Load
              </span>
              <span className="text-cyan-300">{status.cpuLoad}%</span>
            </div>
            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
              <div className="bg-cyan-500 h-full rounded-full transition-all duration-500" style={{ width: `${status.cpuLoad}%` }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-slate-400 mb-1 text-[11px]">
              <span className="flex items-center gap-1">
                <Gauge className="w-3 h-3 text-violet-400" /> RAM Alloc
              </span>
              <span className="text-violet-300">{status.memoryUsage}%</span>
            </div>
            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
              <div className="bg-violet-500 h-full rounded-full transition-all duration-500" style={{ width: `${status.memoryUsage}%` }} />
            </div>
          </div>

          <div className="pt-1 border-t border-slate-800/80 text-[10px] text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1 text-slate-400">
              <Sparkles className="w-3 h-3 text-amber-400" /> Reasoning Engine:
            </span>
            <span className="text-slate-200 truncate max-w-[120px]" title={status.activeModels[0]}>
              {status.activeModels[0]}
            </span>
          </div>
        </div>

      </div>
    </div>
  );
};
