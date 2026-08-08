import React from 'react';
import { Radio, FilterX, Send, Award, TrendingUp } from 'lucide-react';

interface MetricCardsProps {
  signalsCount: number;
  rejectedCount: number;
  publishedCount: number;
  avgEditorialScore: number;
}

export const MetricCards: React.FC<MetricCardsProps> = ({
  signalsCount,
  rejectedCount,
  publishedCount,
  avgEditorialScore,
}) => {
  const cards = [
    {
      title: 'Signals Discovered',
      value: signalsCount,
      trend: '+18.4% velocity',
      isPositive: true,
      icon: Radio,
      color: 'text-cyan-400',
      bgGlow: 'hover:border-cyan-500/50 hover:shadow-[0_0_20px_rgba(6,182,212,0.15)]',
      iconBg: 'bg-cyan-950/80 border-cyan-500/30 text-cyan-400',
      subtext: 'High-confidence tech telemetry',
    },
    {
      title: 'Topics Rejected',
      value: rejectedCount,
      trend: '74% Noise Filtered',
      isPositive: true,
      icon: FilterX,
      color: 'text-amber-400',
      bgGlow: 'hover:border-amber-500/50 hover:shadow-[0_0_20px_rgba(245,158,11,0.15)]',
      iconBg: 'bg-amber-950/80 border-amber-500/30 text-amber-400',
      subtext: 'Duplicate & low-novelty topics',
    },
    {
      title: 'Posts Published',
      value: publishedCount,
      trend: '100% Verified',
      isPositive: true,
      icon: Send,
      color: 'text-emerald-400',
      bgGlow: 'hover:border-emerald-500/50 hover:shadow-[0_0_20px_rgba(16,185,129,0.15)]',
      iconBg: 'bg-emerald-950/80 border-emerald-500/30 text-emerald-400',
      subtext: 'Across Telegram, X & Newsletter',
    },
    {
      title: 'Avg Editorial Score',
      value: `${avgEditorialScore.toFixed(1)} / 10`,
      trend: 'Top 5% Quality Bar',
      isPositive: true,
      icon: Award,
      color: 'text-violet-400',
      bgGlow: 'hover:border-violet-500/50 hover:shadow-[0_0_20px_rgba(139,92,246,0.15)]',
      iconBg: 'bg-violet-950/80 border-violet-500/30 text-violet-400',
      subtext: 'Multi-factor evaluation rating',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`bg-slate-900/90 border border-slate-800 rounded-xl p-4 transition-all duration-300 backdrop-blur-sm ${card.bgGlow}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase tracking-wide">{card.title}</span>
              <div className={`p-2 rounded-lg border ${card.iconBg}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-3 flex items-baseline justify-between">
              <span className={`text-2xl font-bold font-mono tracking-tight text-slate-100`}>
                {card.value}
              </span>
              <span className={`text-xs font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-1 ${card.color}`}>
                <TrendingUp className="w-3 h-3" />
                {card.trend}
              </span>
            </div>

            <p className="text-[11px] text-slate-400 mt-2 font-sans">{card.subtext}</p>
          </div>
        );
      })}
    </div>
  );
};
