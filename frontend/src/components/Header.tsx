import React, { useState, useEffect } from 'react';
import { Shield, RefreshCw, Activity } from 'lucide-react';
import type { NovaAgentStatus } from '../types';

interface HeaderProps {
  status: NovaAgentStatus;
  onTriggerScan: () => void;
  isScanning: boolean;
}

export const Header: React.FC<HeaderProps> = ({ status, onTriggerScan, isScanning }) => {
  const [secondsToNextCycle, setSecondsToNextCycle] = useState<number>(890); // ~14m 50s countdown

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsToNextCycle((prev) => (prev > 0 ? prev - 1 : 900));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatCountdown = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <header className="bg-slate-900/90 border-b border-cyan-950/80 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-8 py-3 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        {/* Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
            <Shield className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-wider text-slate-100 uppercase font-mono">
                SIGNAL<span className="text-cyan-400">FORGE</span>
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                NOVA AI v2.4
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
              <Activity className="w-3 h-3 text-emerald-400 animate-pulse" />
              <span>Autonomous Technology Intelligence Control Center</span>
            </p>
          </div>
        </div>

        {/* Status Badges & Cycle Telemetry */}
        <div className="flex flex-wrap items-center gap-3 lg:gap-6 text-xs font-mono">
          
          {/* Agent State Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Agent Status:</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${isScanning ? 'bg-amber-400 animate-ping' : 'bg-emerald-400 animate-pulse'}`} />
              <span className={`font-semibold ${isScanning ? 'text-amber-400' : 'text-emerald-400'}`}>
                {isScanning ? 'EXECUTING SCAN...' : status.state}
              </span>
            </div>
          </div>

          {/* Last / Next Cycle Info */}
          <div className="hidden sm:flex items-center gap-4 px-3 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-300">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Last Cycle:</span>
              <span className="text-slate-200">{status.lastCycleAt}</span>
            </div>
            <div className="h-3 w-px bg-slate-800" />
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Next Cycle In:</span>
              <span className="text-cyan-400 font-bold">{formatCountdown(secondsToNextCycle)}</span>
            </div>
          </div>

          {/* Trigger Cycle Button */}
          <button
            onClick={onTriggerScan}
            disabled={isScanning}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg font-sans text-xs font-medium transition-all shadow-md ${
              isScanning
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold border border-cyan-400 hover:shadow-[0_0_15px_rgba(6,182,212,0.4)] active:scale-95'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin' : ''}`} />
            <span>{isScanning ? 'Scanning Mesh...' : 'Trigger Cycle'}</span>
          </button>
        </div>

      </div>
    </header>
  );
};
