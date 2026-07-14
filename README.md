# 🛡️ Aegis CRM — AI-First HCP Module
> **Next-Generation CRM for Healthcare Professionals (HCPs) featuring LangGraph Agent-driven interaction logs and real-time form-to-chat synchronization.**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org)
[![Redux](https://img.shields.io/badge/Redux-593D88?style=for-the-badge&logo=redux&logoColor=white)](https://redux.js.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-teal?style=for-the-badge)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Groq_gemma2--9b--it-orange?style=for-the-badge)](https://console.groq.com)
[![MySQL](https://img.shields.io/badge/MySQL-00758F?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com)

---

## 📖 Project Overview

Aegis CRM is an AI-first Healthcare Customer Relationship Management system designed for pharmaceutical and medical field representatives. It offers a dual-method interface that allows representatives to log doctor visits either using a **highly-structured interactive form** or a **conversational AI Assistant**. 

### Key Capabilities
*   **Dual Log Options**: Submit structured details or describe a meeting in natural language.
*   **Conversational Sync**: The LangGraph assistant extracts structured entities from chat messages and immediately auto-populates form fields on the left in real-time.
*   **Smart Seeding**: Automatically checks local environment and configures database tables, seeding mock doctor directories (e.g. Dr. Anita Sharma, Dr. Rajesh Patel) and therapeutic products (e.g., CardiaShield, OncoBoost).
*   **Voice Dictation Simulator**: Reps can simulate dictating a visit details note; the backend extracts topics, products shared, and patient samples distributed.

---

## 🔄 System Interaction Workflow

The diagram below illustrates how structured and conversational logging pathways integrate with FastAPI, the LangGraph Agent, and the MySQL database, updating the frontend state dynamically:

```mermaid
graph TD
    %% User Inputs
    User[Field Representative] -->|1a. Structured Form Input| Form[Structured Form UI]
    User -->|1b. Natural Chat Prompt| Chat[AI Assistant Panel]
    
    %% APIs
    Form -->|POST: /api/interactions| API(FastAPI Backend Router)
    Chat -->|POST: /api/chat| API
    
    %% LangGraph Agent
    API -->|Interact| Graph{LangGraph ReAct Controller}
    
    %% Tools Executed
    Graph -->|Route Intent| Tools[Sales Tools Executor]
    Tools -->|log_interaction| Tool1[log_interaction Tool]
    Tools -->|edit_interaction| Tool2[edit_interaction Tool]
    Tools -->|search_hcp_history| Tool3[search_hcp_history Tool]
    Tools -->|suggest_follow_up| Tool4[suggest_follow_up Tool]
    Tools -->|product_recommendation| Tool5[product_recommendation Tool]
    
    %% DB Synchronization
    Tool1 & Tool2 & Tool3 & Tool4 & Tool5 -->|SQLAlchemy| DB[(MySQL CRM Database)]
    
    %% State Sync
    Tool1 -->|Sync Extracted Fields| Redux[Redux Store State]
    Form -->|Save Success Dispatch| Redux
    Redux -->|Dynamic Form Update| User
    DB -->|Read Historic Log Table| Redux
    
    classDef main fill:#0d1117,stroke:#5eead4,stroke-width:2px,color:#fff;
    classDef tool fill:#1e293b,stroke:#a855f7,stroke-width:1px,color:#f1f5f9;
    classDef db fill:#00758f,stroke:#fff,stroke-width:1.5px,color:#fff;
    class User,Form,Chat,API,Graph,Redux main;
    class Tool1,Tool2,Tool3,Tool4,Tool5 tool;
    class DB db;
```

---

## 🧠 LangGraph Agent Architecture

The AI assistant utilizes a compiled **LangGraph StateGraph** implementing the **ReAct (Reasoning + Action)** pattern.

```
                  ┌──────────────────────┐
                  │   User Message /     │
                  │   Conversation State │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    gemma2-9b-it      │
                  │   (Agent Controller) │
                  └──────────┬───────────┘
                             │
              Is Tool Call Required?
              ┌──────────────┴──────────────┐
              │ Yes                         │ No
              ▼                             ▼
   ┌──────────────────────┐      ┌──────────────────────┐
   │  Tools Node          │      │   Agent Response     │
   │  (Executes: Log,     ├─────►│   (Output to Chat)   │
   │   Edit, Search...)   │      └──────────────────────┘
   └──────────────────────┘
```

### The Role of the Agent in CRM Logging
1.  **State Retention**: Tracks the ongoing chat log (`messages`) along with an active form buffer (`form_draft`).
2.  **Intent Parsing & Slot Filling**: When a rep says *"Met with Dr. Patel today, sentiment positive, discussed oncoboost"* the agent extracts key entities (HCP: Dr. Rajesh Patel, Sentiment: Positive, Topics: Oncology/OncoBoost) and automatically fills the corresponding form draft inputs.
3.  **Autonomous Tool Calling**: Based on instructions, the agent executes appropriate database tools to retrieve context or commit changes without human middleware.

---

## 🛠️ Detailed Tool Implementation

The backend exposes **five specialized sales tools** to LangGraph:

| Tool Name | Parameters | Core Responsibility |
| :--- | :--- | :--- |
| **`log_interaction`** *(Mandatory)* | `hcp_name`, `interaction_type`, `date`, `time`, `topics_discussed`, `sentiment`, `attendees`, `materials_shared`, `samples_distributed` | Resolves doctor name, creates new profile if missing, generates AI summary, and saves the log. |
| **`edit_interaction`** *(Mandatory)* | `interaction_id`, `interaction_type`, `date`, `time`, `attendees`, `topics_discussed`, `sentiment` | Loads an existing database log by ID and overwrites changed fields. |
| **`search_hcp_history`** | `hcp_name` | Queries database for history of meetings, summaries, and shared materials with a physician. |
| **`suggest_follow_up`** | `topics_discussed`, `hcp_specialty` | Generates clinical follow-up recommendations (e.g. email trials brochure in 2 weeks, deliver multivitamin samples). |
| **`product_recommendation`**| `hcp_specialty` | Matches physician specialty against products table, returning recommendations for sales details. |

---

## 📁 Directory Structure

```
c:\Users\ROHIT\Desktop\Ai task\
│
├── backend/
│   ├── app/
│   │   ├── agent.py       # LangGraph StateGraph, Tools, and Fallback simulator
│   │   ├── database.py    # SQLAlchemy schema configurations and default seeding
│   │   ├── main.py        # FastAPI server endpoints, CORS headers, Voice summaries
│   │   └── schemas.py     # Pydantic validation schemas
│   │
│   ├── .env               # Database credentials & Groq API key configuration
│   ├── requirements.txt   # Python requirements list
│   └── test_agent.py      # Local automated database and agent tool test suite
│
├── frontend/
│   ├── public/
│   │   └── index.html     # HTML bootstrap document loading Google Inter font
│   ├── src/
│   │   ├── components/
│   │   │   ├── AIAssistant.js      # Chat bubble component with typing shimmer
│   │   │   ├── Header.js           # Premium statistics summary navbar
│   │   │   └── InteractionForm.js  # Form inputs, autocomplete list, and dictation modal
│   │   ├── store/
│   │   │   ├── index.js            # Redux store config
│   │   │   └── interactionSlice.js # State variables, actions, and fetch thunks
│   │   ├── App.js                  # Main dashboard viewport and logs list table
│   │   └── index.css               # Global glassmorphism style sheet
│   └── package.json       # React and Redux scripts
│
└── README.md              # Project documentation
```

---

## 🚀 Setup & Execution Guide

### 1. Database Configuration
By default, the backend checks for a local MySQL service (attempts connection using `root` and default passwords). 
*   It automatically creates the database `hcp_crm`.
*   It seeds the tables with default doctor records and therapeutic details.
*   **SQLite Fallback**: If no MySQL server is reachable, it automatically writes to a local fail-safe SQLite database (`sqlite:///hcp_crm.db`), ensuring the application starts immediately without crashing.

### 2. Launch FastAPI Backend
1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Configure your environment values by creating a `.env` file:
   ```env
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/hcp_crm
   GROQ_API_KEY=your_groq_api_key
   ```
   > [!NOTE]
   > *If no Groq API Key is configured, a rule-based NLP agent simulator will automatically handle chat events and tool executions, keeping the application fully functional for local evaluation.*
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *Swagger API documents will be available at: http://localhost:8000/docs*

### 3. Launch React Frontend
1. Open a separate terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the React server:
   ```bash
   npm start
   ```
   *The page will compile and render at: http://localhost:3000*
