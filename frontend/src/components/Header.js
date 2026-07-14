import React from 'react';
import { useSelector } from 'react-redux';
import { Activity, ShieldAlert, CheckCircle, BarChart3, Database } from 'lucide-react';

export default function Header() {
  const { interactions } = useSelector(state => state.interactions);
  
  // Calculate simple stats
  const total = interactions.length;
  const positive = interactions.filter(i => i.sentiment === 'Positive').length;
  const neutral = interactions.filter(i => i.sentiment === 'Neutral').length;
  const negative = interactions.filter(i => i.sentiment === 'Negative').length;

  return (
    <header className="w-full flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 mb-4 border-b border-white/10">
      {/* Brand Logo and Title */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-teal-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
          <Activity className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Aegis CRM</h1>
            <span className="text-[10px] uppercase font-bold tracking-wider py-0.5 px-2 bg-teal-500/10 text-teal-300 rounded-full border border-teal-500/20">
              HCP Module
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-0.5">AI-First Healthcare Representative Interaction Logger</p>
        </div>
      </div>

      {/* Stats Summary Bar */}
      <div className="flex flex-wrap items-center gap-3 md:gap-4 bg-white/5 border border-white/10 rounded-2xl p-3 max-w-full overflow-hidden">
        <div className="flex items-center gap-2 border-r border-white/10 pr-3 md:pr-4">
          <Database className="w-4 h-4 text-slate-400" />
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Logs</div>
            <div className="text-sm font-semibold text-white">{total}</div>
          </div>
        </div>
        
        <div className="flex items-center gap-2 border-r border-white/10 pr-3 md:pr-4">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Positive</div>
            <div className="text-sm font-semibold text-white">{positive}</div>
          </div>
        </div>
        
        <div className="flex items-center gap-2 border-r border-white/10 pr-3 md:pr-4">
          <span className="w-2 h-2 rounded-full bg-amber-500"></span>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Neutral</div>
            <div className="text-sm font-semibold text-white">{neutral}</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-rose-500"></span>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Negative</div>
            <div className="text-sm font-semibold text-white">{negative}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
