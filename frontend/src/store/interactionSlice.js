import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const API_BASE = 'http://localhost:8000/api';

// Initial state for form fields
const initialFormState = {
  hcp_id: '',
  hcp_name: '',
  interaction_type: 'Meeting',
  date: new Date().toISOString().split('T')[0],
  time: new Date().toTimeString().slice(0, 5),
  attendees: '',
  topics_discussed: '',
  voice_note_summary: '',
  materials_shared: '',
  samples_distributed: '',
  sentiment: 'Neutral',
  outcomes: '',
  follow_up_actions: '',
  ai_summary: ''
};

// Async Thunks
export const fetchHCPs = createAsyncThunk('interactions/fetchHCPs', async (_, { rejectWithValue }) => {
  try {
    const response = await fetch(`${API_BASE}/hcps`);
    if (!response.ok) throw new Error('Failed to fetch HCPs');
    return await response.json();
  } catch (err) {
    return rejectWithValue(err.message);
  }
});

export const fetchProducts = createAsyncThunk('interactions/fetchProducts', async (_, { rejectWithValue }) => {
  try {
    const response = await fetch(`${API_BASE}/products`);
    if (!response.ok) throw new Error('Failed to fetch products');
    return await response.json();
  } catch (err) {
    return rejectWithValue(err.message);
  }
});

export const fetchInteractions = createAsyncThunk('interactions/fetchInteractions', async (_, { rejectWithValue }) => {
  try {
    const response = await fetch(`${API_BASE}/interactions`);
    if (!response.ok) throw new Error('Failed to fetch interactions');
    return await response.json();
  } catch (err) {
    return rejectWithValue(err.message);
  }
});

export const saveInteraction = createAsyncThunk(
  'interactions/saveInteraction',
  async (interactionData, { rejectWithValue, dispatch }) => {
    try {
      const response = await fetch(`${API_BASE}/interactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(interactionData)
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save interaction');
      }
      const data = await response.json();
      dispatch(fetchInteractions());
      return data;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const updateExistingInteraction = createAsyncThunk(
  'interactions/updateExistingInteraction',
  async ({ id, data }, { rejectWithValue, dispatch }) => {
    try {
      const response = await fetch(`${API_BASE}/interactions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed to update interaction');
      const resData = await response.json();
      dispatch(fetchInteractions());
      return resData;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const deleteExistingInteraction = createAsyncThunk(
  'interactions/deleteExistingInteraction',
  async (id, { rejectWithValue, dispatch }) => {
    try {
      const response = await fetch(`${API_BASE}/interactions/${id}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete interaction');
      dispatch(fetchInteractions());
      return id;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const sendChatMessage = createAsyncThunk(
  'interactions/sendChatMessage',
  async ({ message, history, formDraft }, { rejectWithValue }) => {
    try {
      const payload = {
        message,
        history: history.map(h => ({
          role: h.role,
          content: h.content
        })),
        form_draft: formDraft
      };
      
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error('Failed to get chat response from LangGraph agent');
      return await response.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const summarizeVoiceNote = createAsyncThunk(
  'interactions/summarizeVoiceNote',
  async (transcription, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE}/voice-summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcription })
      });
      if (!response.ok) throw new Error('Failed to analyze voice note transcription');
      const data = await response.json();
      return data.extracted_fields;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

const interactionSlice = createSlice({
  name: 'interactions',
  initialState: {
    hcps: [],
    products: [],
    interactions: [],
    formDraft: initialFormState,
    chatHistory: [
      {
        role: 'assistant',
        content: "Hello! I am your AI HCP CRM Assistant. Describe a meeting (e.g. *'I met with Dr. Rajesh Patel today. We discussed oncology clinical trials'*), and I will help fill the form and log it for you. You can also search doctor history or request recommendations!"
      }
    ],
    isLoading: false,
    isChatLoading: false,
    error: null,
    editingInteractionId: null
  },
  reducers: {
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      state.formDraft[field] = value;
      
      // Auto-resolve hcp_id if hcp_name is selected from dropdown
      if (field === 'hcp_name') {
        const found = state.hcps.find(h => h.name === value);
        if (found) {
          state.formDraft.hcp_id = found.id;
        } else {
          state.formDraft.hcp_id = '';
        }
      }
    },
    resetForm: (state) => {
      state.formDraft = initialFormState;
      state.editingInteractionId = null;
    },
    setFormDraft: (state, action) => {
      state.formDraft = { ...state.formDraft, ...action.payload };
      if (action.payload.hcp_name) {
        const found = state.hcps.find(h => h.name === action.payload.hcp_name);
        if (found) {
          state.formDraft.hcp_id = found.id;
        }
      }
    },
    startEditingInteraction: (state, action) => {
      const inter = action.payload;
      state.editingInteractionId = inter.id;
      state.formDraft = {
        hcp_id: inter.hcp_id,
        hcp_name: inter.hcp.name,
        interaction_type: inter.interaction_type,
        date: inter.date,
        time: inter.time,
        attendees: inter.attendees || '',
        topics_discussed: inter.topics_discussed,
        voice_note_summary: inter.voice_note_summary || '',
        materials_shared: inter.materials_shared || '',
        samples_distributed: inter.samples_distributed || '',
        sentiment: inter.sentiment,
        outcomes: inter.outcomes || '',
        follow_up_actions: inter.follow_up_actions || '',
        ai_summary: inter.ai_summary || ''
      };
    },
    addChatMessage: (state, action) => {
      state.chatHistory.push(action.payload);
    },
    clearChatHistory: (state) => {
      state.chatHistory = [
        {
          role: 'assistant',
          content: "Hello! I am your AI HCP CRM Assistant. Tell me details about your recent visit, and I will parse them, fill out the form, and register the log in our system."
        }
      ];
    }
  },
  extraReducers: (builder) => {
    // Fetch HCPs
    builder.addCase(fetchHCPs.fulfilled, (state, action) => {
      state.hcps = action.payload;
    });
    // Fetch Products
    builder.addCase(fetchProducts.fulfilled, (state, action) => {
      state.products = action.payload;
    });
    // Fetch Interactions
    builder.addCase(fetchInteractions.pending, (state) => {
      state.isLoading = true;
    });
    builder.addCase(fetchInteractions.fulfilled, (state, action) => {
      state.isLoading = false;
      state.interactions = action.payload;
    });
    builder.addCase(fetchInteractions.rejected, (state, action) => {
      state.isLoading = false;
      state.error = action.payload;
    });
    // Save Interaction
    builder.addCase(saveInteraction.pending, (state) => {
      state.isLoading = true;
    });
    builder.addCase(saveInteraction.fulfilled, (state) => {
      state.isLoading = false;
      state.formDraft = initialFormState;
      state.editingInteractionId = null;
    });
    builder.addCase(saveInteraction.rejected, (state, action) => {
      state.isLoading = false;
      state.error = action.payload;
    });
    // Send Chat Message
    builder.addCase(sendChatMessage.pending, (state) => {
      state.isChatLoading = true;
    });
    builder.addCase(sendChatMessage.fulfilled, (state, action) => {
      state.isChatLoading = false;
      const { reply, form_draft } = action.payload;
      
      // Add assistant response to history
      state.chatHistory.push({
        role: 'assistant',
        content: reply
      });
      
      // Update form draft values if assistant extracted them
      if (form_draft) {
        // Merge extracted fields
        Object.keys(form_draft).forEach(key => {
          if (form_draft[key] !== undefined && form_draft[key] !== null && form_draft[key] !== "") {
            state.formDraft[key] = form_draft[key];
          }
        });
        
        // Resolve hcp_id
        if (form_draft.hcp_name) {
          const found = state.hcps.find(h => h.name === form_draft.hcp_name);
          if (found) {
            state.formDraft.hcp_id = found.id;
          }
        }
      }
    });
    builder.addCase(sendChatMessage.rejected, (state, action) => {
      state.isChatLoading = false;
      state.error = action.payload;
      state.chatHistory.push({
        role: 'assistant',
        content: "Sorry, I encountered an error communicating with the agent server."
      });
    });
    // Summarize Voice Note
    builder.addCase(summarizeVoiceNote.fulfilled, (state, action) => {
      const extracted = action.payload;
      if (extracted) {
        Object.keys(extracted).forEach(key => {
          if (extracted[key]) {
            state.formDraft[key] = extracted[key];
          }
        });
        if (extracted.hcp_name) {
          const found = state.hcps.find(h => h.name === extracted.hcp_name);
          if (found) {
            state.formDraft.hcp_id = found.id;
          }
        }
      }
    });
  }
});

export const { updateFormField, resetForm, setFormDraft, startEditingInteraction, addChatMessage, clearChatHistory } = interactionSlice.actions;
export default interactionSlice.reducer;
