import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  updateFormField, 
  saveInteraction, 
  updateExistingInteraction,
  resetForm, 
  summarizeVoiceNote, 
  setFormDraft 
} from '../store/interactionSlice';
import { 
  Calendar, Clock, Users, FileText, Smile, CheckSquare, 
  Plus, X, Mic, RefreshCw, AlertCircle, Bookmark 
} from 'lucide-react';

export default function InteractionForm() {
  const dispatch = useDispatch();
  const { formDraft, hcps, products, editingInteractionId, isLoading } = useSelector(state => state.interactions);
  
  // Voice note simulation state
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [voiceText, setVoiceText] = useState('');
  const [isVoiceLoading, setIsVoiceLoading] = useState(false);

  // Search/add custom materials and samples
  const [materialInput, setMaterialInput] = useState('');
  const [sampleInput, setSampleInput] = useState('');

  // Dropdown list for selection
  const materialsList = products.filter(p => p.category === 'Material');
  const samplesList = products.filter(p => p.category === 'Sample');

  // Handle voice note submit
  const handleVoiceSubmit = async () => {
    if (!voiceText.trim()) return;
    setIsVoiceLoading(true);
    await dispatch(summarizeVoiceNote(voiceText));
    setIsVoiceLoading(false);
    setShowVoiceModal(false);
    setVoiceText('');
  };

  // Add material
  const addMaterial = (name) => {
    if (!name) return;
    const current = formDraft.materials_shared ? formDraft.materials_shared.split(', ') : [];
    if (!current.includes(name)) {
      const updated = [...current, name].join(', ');
      dispatch(updateFormField({ field: 'materials_shared', value: updated }));
    }
    setMaterialInput('');
  };

  // Remove material
  const removeMaterial = (name) => {
    const current = formDraft.materials_shared ? formDraft.materials_shared.split(', ') : [];
    const updated = current.filter(m => m !== name).join(', ');
    dispatch(updateFormField({ field: 'materials_shared', value: updated }));
  };

  // Add sample
  const addSample = (name) => {
    if (!name) return;
    const current = formDraft.samples_distributed ? formDraft.samples_distributed.split(', ') : [];
    if (!current.includes(name)) {
      const updated = [...current, name].join(', ');
      dispatch(updateFormField({ field: 'samples_distributed', value: updated }));
    }
    setSampleInput('');
  };

  // Remove sample
  const removeSample = (name) => {
    const current = formDraft.samples_distributed ? formDraft.samples_distributed.split(', ') : [];
    const updated = current.filter(s => s !== name).join(', ');
    dispatch(updateFormField({ field: 'samples_distributed', value: updated }));
  };

  // Handle Suggested Follow-up click
  const handleSuggestedClick = (text) => {
    const current = formDraft.follow_up_actions ? formDraft.follow_up_actions.trim() : '';
    const separator = current ? '\n' : '';
    const updated = `${current}${separator}• ${text}`;
    dispatch(updateFormField({ field: 'follow_up_actions', value: updated }));
  };

  // Submit the main form
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formDraft.hcp_name) {
      alert('Please select or enter an HCP Name');
      return;
    }
    
    // Resolve hcp_id if not set but name matches existing
    let hcp_id = formDraft.hcp_id;
    if (!hcp_id) {
      const matched = hcps.find(h => h.name.toLowerCase() === formDraft.hcp_name.toLowerCase());
      hcp_id = matched ? matched.id : null;
    }

    // If new HCP, we need to register HCP first or backend creates it
    const payload = {
      ...formDraft,
      hcp_id: hcp_id || 0 // Backend handles 0 by creating HCP
    };

    if (editingInteractionId) {
      dispatch(updateExistingInteraction({ id: editingInteractionId, data: payload }));
    } else {
      dispatch(saveInteraction(payload));
    }
  };

  return (
    <div className="glass-card p-6 flex flex-col gap-6 relative overflow-hidden">
      {/* Glow Effect */}
      <div className="absolute -top-24 -left-24 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>
      
      <div className="flex justify-between items-center pb-4 border-b border-white/10 z-10">
        <h2 className="text-xl font-semibold flex items-center gap-2 text-white">
          <Bookmark className="text-teal-400 w-5 h-5" />
          {editingInteractionId ? 'Edit Interaction Details' : 'Interaction Details'}
        </h2>
        {editingInteractionId && (
          <button 
            type="button" 
            onClick={() => dispatch(resetForm())}
            className="text-xs py-1 px-3 rounded-full bg-white/5 hover:bg-white/10 text-slate-300 transition"
          >
            Cancel Edit
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5 z-10">
        {/* HCP Name & Interaction Type Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300">HCP Name</label>
            <div className="relative">
              <input
                type="text"
                list="hcps-list"
                value={formDraft.hcp_name}
                onChange={(e) => dispatch(updateFormField({ field: 'hcp_name', value: e.target.value }))}
                placeholder="Search or select HCP..."
                className="input-field w-full"
                required
              />
              <datalist id="hcps-list">
                {hcps.map(hcp => (
                  <option key={hcp.id} value={hcp.name}>{hcp.specialty}</option>
                ))}
              </datalist>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300">Interaction Type</label>
            <select
              value={formDraft.interaction_type}
              onChange={(e) => dispatch(updateFormField({ field: 'interaction_type', value: e.target.value }))}
              className="input-field select-field w-full"
            >
              <option value="Meeting">Meeting</option>
              <option value="Call">Call</option>
              <option value="Email">Email</option>
              <option value="Webcast">Webcast</option>
            </select>
          </div>
        </div>

        {/* Date & Time Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-teal-400" /> Date
            </label>
            <input
              type="date"
              value={formDraft.date}
              onChange={(e) => dispatch(updateFormField({ field: 'date', value: e.target.value }))}
              className="input-field w-full"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-teal-400" /> Time
            </label>
            <input
              type="time"
              value={formDraft.time}
              onChange={(e) => dispatch(updateFormField({ field: 'time', value: e.target.value }))}
              className="input-field w-full"
              required
            />
          </div>
        </div>

        {/* Attendees */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
            <Users className="w-3.5 h-3.5 text-teal-400" /> Attendees
          </label>
          <input
            type="text"
            value={formDraft.attendees}
            onChange={(e) => dispatch(updateFormField({ field: 'attendees', value: e.target.value }))}
            placeholder="Enter names or search..."
            className="input-field"
          />
        </div>

        {/* Topics Discussed */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-teal-400" /> Topics Discussed
          </label>
          <textarea
            value={formDraft.topics_discussed}
            onChange={(e) => dispatch(updateFormField({ field: 'topics_discussed', value: e.target.value }))}
            placeholder="Enter discussion points..."
            className="input-field min-h-[80px]"
            required
          />
          <button
            type="button"
            onClick={() => setShowVoiceModal(true)}
            className="flex items-center justify-center gap-1.5 self-start text-xs font-medium py-1.5 px-3 rounded-full bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 transition mt-1 border border-teal-500/20"
          >
            <Mic className="w-3.5 h-3.5 animate-pulse" />
            Summarize from Voice Note (Requires Consent)
          </button>
        </div>

        {/* Materials & Samples Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Materials Shared */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300">Materials Shared</label>
            <div className="flex gap-2">
              <input
                type="text"
                list="materials-suggest"
                value={materialInput}
                onChange={(e) => setMaterialInput(e.target.value)}
                placeholder="Search/Add material..."
                className="input-field flex-1"
                onKeyDown={(e) => { if(e.key === 'Enter') { e.preventDefault(); addMaterial(materialInput); }}}
              />
              <datalist id="materials-suggest">
                {materialsList.map(m => <option key={m.id} value={m.name} />)}
              </datalist>
              <button
                type="button"
                onClick={() => addMaterial(materialInput)}
                className="py-2 px-3 bg-teal-500/20 text-teal-300 hover:bg-teal-500/30 rounded-lg transition border border-teal-500/30"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            {/* Tag List */}
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {formDraft.materials_shared && formDraft.materials_shared.split(', ').map(item => (
                <span key={item} className="inline-flex items-center gap-1 text-[11px] font-medium bg-white/5 border border-white/15 px-2 py-0.5 rounded-full text-slate-200">
                  {item}
                  <button type="button" onClick={() => removeMaterial(item)} className="hover:text-red-400">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Samples Distributed */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300">Samples Distributed</label>
            <div className="flex gap-2">
              <input
                type="text"
                list="samples-suggest"
                value={sampleInput}
                onChange={(e) => setSampleInput(e.target.value)}
                placeholder="Add sample..."
                className="input-field flex-1"
                onKeyDown={(e) => { if(e.key === 'Enter') { e.preventDefault(); addSample(sampleInput); }}}
              />
              <datalist id="samples-suggest">
                {samplesList.map(s => <option key={s.id} value={s.name} />)}
              </datalist>
              <button
                type="button"
                onClick={() => addSample(sampleInput)}
                className="py-2 px-3 bg-teal-500/20 text-teal-300 hover:bg-teal-500/30 rounded-lg transition border border-teal-500/30"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            {/* Tag List */}
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {formDraft.samples_distributed && formDraft.samples_distributed.split(', ').map(item => (
                <span key={item} className="inline-flex items-center gap-1 text-[11px] font-medium bg-white/5 border border-white/15 px-2 py-0.5 rounded-full text-slate-200">
                  {item}
                  <button type="button" onClick={() => removeSample(item)} className="hover:text-red-400">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Observed/Inferred HCP Sentiment */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
            <Smile className="w-3.5 h-3.5 text-teal-400" /> Observed/Inferred HCP Sentiment
          </label>
          <div className="flex gap-4">
            {['Positive', 'Neutral', 'Negative'].map(val => (
              <label key={val} className="inline-flex items-center gap-2 cursor-pointer text-sm text-slate-300">
                <input
                  type="radio"
                  name="sentiment"
                  value={val}
                  checked={formDraft.sentiment === val}
                  onChange={() => dispatch(updateFormField({ field: 'sentiment', value: val }))}
                  className="accent-teal-500 w-4 h-4"
                />
                {val}
              </label>
            ))}
          </div>
        </div>

        {/* Outcomes */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-300">Outcomes</label>
          <textarea
            value={formDraft.outcomes}
            onChange={(e) => dispatch(updateFormField({ field: 'outcomes', value: e.target.value }))}
            placeholder="Key outcomes or agreements..."
            className="input-field min-h-[60px]"
          />
        </div>

        {/* Follow-up Actions */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
            <CheckSquare className="w-3.5 h-3.5 text-teal-400" /> Follow-up Actions
          </label>
          <textarea
            value={formDraft.follow_up_actions}
            onChange={(e) => dispatch(updateFormField({ field: 'follow_up_actions', value: e.target.value }))}
            placeholder="Enter next steps or tasks..."
            className="input-field min-h-[60px]"
          />
        </div>

        {/* AI Suggested Follow-ups */}
        <div className="flex flex-col gap-2 p-3 bg-white/5 border border-white/10 rounded-xl">
          <span className="text-[11px] font-bold text-teal-400 tracking-wide uppercase">AI Suggested Follow-ups</span>
          <div className="flex flex-col gap-1.5 mt-1">
            {[
              "Schedule follow-up meeting in 2 weeks",
              "Send OncoBoost Phase III trial data PDF",
              "Add Dr. Sharma to advisory board invite list"
            ].map(suggested => (
              <button
                type="button"
                key={suggested}
                onClick={() => handleSuggestedClick(suggested)}
                className="text-left text-xs text-slate-300 hover:text-teal-300 transition flex items-center gap-1"
              >
                <Plus className="w-3 h-3 text-teal-500" /> {suggested}
              </button>
            ))}
          </div>
        </div>

        {/* AI summary (if generated) */}
        {formDraft.ai_summary && (
          <div className="p-3 bg-teal-500/10 border border-teal-500/20 rounded-xl flex flex-col gap-1 text-slate-300">
            <span className="text-[10px] font-bold text-teal-300 tracking-wide uppercase flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> AI Summary & Entities
            </span>
            <p className="text-xs italic leading-relaxed">{formDraft.ai_summary}</p>
          </div>
        )}

        {/* Save/Edit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white font-medium shadow-lg hover:shadow-teal-500/25 transition flex justify-center items-center gap-2"
        >
          {isLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : editingInteractionId ? (
            'Save Changes'
          ) : (
            'Log Interaction'
          )}
        </button>
      </form>

      {/* Voice Note Simulation Modal */}
      {showVoiceModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-md w-full p-6 flex flex-col gap-4 border border-teal-500/20 shadow-2xl">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-lg text-white flex items-center gap-2">
                <Mic className="text-teal-400 w-5 h-5 animate-pulse" />
                Simulate Voice Note Transcription
              </h3>
              <button onClick={() => setShowVoiceModal(false)} className="hover:text-red-400">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            
            <p className="text-xs text-slate-300 leading-relaxed">
              To test the voice note summarization feature, type or paste the transcription text of the doctor visit below (e.g. *“I visited Dr. Rajesh Patel at oncology today. The discussion went well. He was excited about OncoBoost samples and asked for the clinical PDF. Follow up next week.”*).
            </p>

            <textarea
              value={voiceText}
              onChange={(e) => setVoiceText(e.target.value)}
              placeholder="Paste simulated dictation / voice transcription..."
              className="input-field min-h-[120px] w-full"
            />

            <div className="flex gap-2 justify-end mt-2">
              <button
                type="button"
                onClick={() => setShowVoiceModal(false)}
                className="py-2 px-4 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-sm font-medium transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleVoiceSubmit}
                disabled={isVoiceLoading || !voiceText.trim()}
                className="py-2 px-4 rounded-lg bg-teal-500 hover:bg-teal-600 text-white text-sm font-medium transition flex items-center gap-1.5 shadow-md shadow-teal-500/20"
              >
                {isVoiceLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
                Analyze and Auto-fill
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
