import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  fetchHCPs, 
  fetchProducts, 
  fetchInteractions, 
  deleteExistingInteraction, 
  startEditingInteraction 
} from './store/interactionSlice';
import Header from './components/Header';
import InteractionForm from './components/InteractionForm';
import AIAssistant from './components/AIAssistant';
import { Edit3, Trash2, Calendar, Clock, Smile, Tag, ShieldCheck, User } from 'lucide-react';

export default function App() {
  const dispatch = useDispatch();
  const { interactions, isLoading, error } = useSelector(state => state.interactions);

  // Load initial data on mount
  useEffect(() => {
    dispatch(fetchHCPs());
    dispatch(fetchProducts());
    dispatch(fetchInteractions());
  }, [dispatch]);

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this interaction log?')) {
      dispatch(deleteExistingInteraction(id));
    }
  };

  const handleEdit = (inter) => {
    dispatch(startEditingInteraction(inter));
    // Scroll to the top of the form
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'Positive': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'Negative': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default: return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8 flex flex-col gap-6">
      {/* Header component */}
      <Header />

      {/* Main dashboard columns */}
      <div className="dashboard-grid">
        {/* Left Form */}
        <InteractionForm />

        {/* Right Assistant */}
        <AIAssistant />
      </div>

      {/* Previously Logged Interactions Table */}
      <div className="glass-card p-6 flex flex-col gap-4 relative overflow-hidden mt-6">
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
        
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="text-emerald-400 w-5 h-5" />
          Logged CRM Interactions
        </h2>

        {isLoading && interactions.length === 0 ? (
          <div className="text-center py-10 text-slate-400 text-sm">
            Loading logged interactions...
          </div>
        ) : error ? (
          <div className="text-center py-10 text-rose-400 text-sm bg-rose-500/5 rounded-xl border border-rose-500/10">
            Error loading logs: {error}
          </div>
        ) : interactions.length === 0 ? (
          <div className="text-center py-10 text-slate-400 text-sm italic">
            No interactions logged yet. Log your first visit using the form or AI chat.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-white/10">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/5 text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-white/10">
                  <th className="p-4">HCP & Specialty</th>
                  <th className="p-4">Type</th>
                  <th className="p-4">Date & Time</th>
                  <th className="p-4">Discussion & AI Summary</th>
                  <th className="p-4">Sentiment</th>
                  <th className="p-4">Shared Materials</th>
                  <th className="p-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {interactions.map(inter => (
                  <tr key={inter.id} className="hover:bg-white/5 transition">
                    <td className="p-4">
                      <div className="font-semibold text-white flex items-center gap-1.5">
                        <User className="w-4 h-4 text-teal-400" />
                        {inter.hcp.name}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">{inter.hcp.specialty}</div>
                    </td>
                    <td className="p-4">
                      <span className="inline-block py-0.5 px-2.5 rounded-full text-xs font-medium bg-white/5 border border-white/15 text-slate-200">
                        {inter.interaction_type}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-1 text-slate-300">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        {inter.date}
                      </div>
                      <div className="flex items-center gap-1 text-slate-400 text-xs mt-1">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        {inter.time}
                      </div>
                    </td>
                    <td className="p-4 max-w-xs md:max-w-md">
                      <div className="font-medium text-slate-200 line-clamp-1">{inter.topics_discussed}</div>
                      {inter.ai_summary && (
                        <div className="text-xs text-teal-300/80 italic mt-1 line-clamp-2 bg-teal-500/5 p-1.5 rounded border border-teal-500/10">
                          {inter.ai_summary}
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      <span className={`inline-flex items-center gap-1 py-0.5 px-2.5 rounded-full text-xs font-semibold border ${getSentimentColor(inter.sentiment)}`}>
                        <Smile className="w-3 h-3" />
                        {inter.sentiment}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex flex-col gap-1 max-w-[180px]">
                        {inter.materials_shared && inter.materials_shared.split(', ').map(m => (
                          <span key={m} className="inline-flex items-center gap-1 text-[10px] bg-teal-500/5 text-teal-300 border border-teal-500/15 py-0.5 px-1.5 rounded">
                            <Tag className="w-2.5 h-2.5" /> {m}
                          </span>
                        ))}
                        {inter.samples_distributed && inter.samples_distributed.split(', ').map(s => (
                          <span key={s} className="inline-flex items-center gap-1 text-[10px] bg-purple-500/5 text-purple-300 border border-purple-500/15 py-0.5 px-1.5 rounded">
                            <Tag className="w-2.5 h-2.5" /> {s} (Sample)
                          </span>
                        ))}
                        {!inter.materials_shared && !inter.samples_distributed && (
                          <span className="text-slate-500 text-xs italic">None</span>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleEdit(inter)}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-teal-500/10 text-slate-300 hover:text-teal-400 transition"
                          title="Edit Interaction"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(inter.id)}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-rose-500/10 text-slate-300 hover:text-rose-400 transition"
                          title="Delete Interaction"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
