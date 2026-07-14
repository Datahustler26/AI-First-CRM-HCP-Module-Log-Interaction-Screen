# Aegis CRM - Healthcare Professional (HCP) Module

A premium, AI-first Customer Relationship Management (CRM) interaction logging screen for Healthcare Professionals (HCPs) and medical/pharmaceutical field representatives. 

This repository allows reps to log interactions using either a **structured, interactive form** or an **AI conversational assistant**. Both pathways sync to a local MySQL database, parse discussion points, run clinical recommendation checks, suggest follow-up actions, and extract entities (doctor name, products discussed, sentiment, outcomes) using LangGraph and the Groq LLM API.

---

## Technical Architecture & Agent Role

### 1. The Role of the LangGraph Agent
The AI assistant is built using **LangGraph (ReAct Graph)**. The LangGraph agent serves as an autonomous controller that:
1. **Understands Intent**: Receives natural language input from the field representative (e.g. *"I met with Dr. Rajesh Patel today. We discussed oncology clinical trials and the sentiment was positive. Outcomes: agreed to meet next month."*).
2. **Dynamic Tool Resolution**: Understands the user's request and routes execution dynamically to one or more of its 5 specialized sales tools.
3. **State Management**: Orchestrates complex conversation state, including keeping a local draft (`form_draft`) in sync. When details are extracted from chat, they are synchronized to the structured React form in real-time, letting the user verify fields before committing.
4. **Returns Formatted Summaries**: Provides a professional Markdown response to the UI, highlighting what actions were taken.

### 2. LangGraph Tools Implemented (5 Tools)
*   `log_interaction` *(Mandatory)*: Resolves the HCP in the database (creating a profile if new), extracts details (products, dates, attendees), uses the LLM to generate a concise summary, and saves the log to the database.
*   `edit_interaction` *(Mandatory)*: Retrieves an existing interaction by ID and applies modifications (e.g., updating sentiment or outcomes) before persisting.
*   `search_hcp_history` *(Sales Tool)*: Retrieves all historical interactions, shared materials, and notes for a specific doctor, summarizing relationship health.
*   `suggest_follow_up` *(Sales Tool)*: Analyzes the topics discussed and recommends standard next steps (e.g., scheduling checkups, inviting to webcasts).
*   `product_recommendation` *(Sales Tool)*: Recommends promotional materials and samples to distribute based on the HCP's medical specialty.

---

## Technology Stack
*   **Frontend**: React.js, Redux (State Management), Google Inter Font, Lucide Icons, Glassmorphic Styling
*   **Backend**: Python, FastAPI, SQLAlchemy, PyMySQL
*   **AI Agent**: LangGraph, LangChain, Groq LLM API (`gemma2-9b-it`)
*   **Database**: MySQL (`MySQL80` service running locally, automatically seeds default database)

---

## Directory Structure
```
c:\Users\ROHIT\Desktop\Ai task\
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── agent.py       # LangGraph agent graph, tools, and fallback simulator
│   │   ├── database.py    # SQLAlchemy tables, connections, and seed logic
│   │   ├── main.py        # FastAPI routes, CORS, and transcription API
│   │   └── schemas.py     # Pydantic validation models
│   │
│   ├── .env               # Backend environment variables
│   ├── requirements.txt   # Python dependencies
│   └── test_agent.py      # Automated agent and database verification script
│
├── frontend/
│   ├── public/
│   │   └── index.html     # HTML entry template (with Inter Font)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AIAssistant.js      # Chat interface & Log submission panel
│   │   │   ├── Header.js           # Premium statistics navbar
│   │   │   └── InteractionForm.js  # Form fields, materials tag lists, and voice dictation modal
│   │   ├── store/
│   │   │   ├── index.js            # Redux store config
│   │   │   └── interactionSlice.js # Redux actions, thunks, and state selectors
│   │   ├── App.css
│   │   ├── App.js                  # Main dashboard layout and logged records table
│   │   ├── index.css               # Global glassmorphic design variables
│   │   └── index.js                # App bootsrapper
│   └── package.json       # React and Redux dependencies
│
└── README.md              # Project documentation
```

---

## Setup & Running Instructions

### 1. Database Configuration
Ensure your local MySQL service is running. The backend is configured to dynamically check multiple database URLs (including password fallbacks like `root:@localhost` or `root:root`) and will automatically create the database `hcp_crm` and seed it with mock doctors (e.g., Dr. Anita Sharma, Dr. Rajesh Patel) and products.
*If all MySQL connection strategies fail, the app will automatically write to a local fail-safe SQLite database (`sqlite:///hcp_crm.db`) to ensure the server starts seamlessly.*

### 2. Run the Backend
1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your API key in `.env` (optional but recommended for LLM agent execution):
   Create/edit the `.env` file in the `backend/` folder:
   ```env
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/hcp_crm
   GROQ_API_KEY=your_groq_api_key_here
   ```
   *Note: If no valid Groq key is supplied, a rule-based NLP agent simulator will automatically handle state management and tools execution to keep the app fully operational.*
4. Start the FastAPI server using Uvicorn:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The Swagger interactive documentation will be available at: http://localhost:8000/docs*

### 3. Run the Frontend
1. Open a new terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Start the React development server:
   ```bash
   npm start
   ```
   *The application will open in your browser at: http://localhost:3000*
