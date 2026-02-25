# NL2SQL Data Analysis Assistant

An intelligent data analysis system that converts natural language questions into SQL queries, executes them against a SQLite database, and presents results with AI-powered analysis and auto-generated visualizations — all in real-time via SSE streaming.

Built with **FastAPI** + **React** + **LangChain** + **Alibaba Cloud Qwen3 LLM**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Natural Language to SQL** — Ask questions in plain Chinese; the system generates and executes SQL automatically
- **SSE Streaming** — Real-time step-by-step feedback: SQL generation → query execution → AI analysis → chart rendering
- **AI Data Analysis** — LLM-powered insights with Markdown rendering (bold highlights, lists, headings)
- **Auto Visualization** — Automatic chart type recommendation and ECharts rendering (bar, line, pie, scatter)
- **Session Management** — Persistent conversation history with context memory (last 10 rounds)
- **Cyberpunk UI** — Dark-themed interface with neon accents, glowing effects, and smooth animations

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌──────────────┬───────────────────┬────────────────────────┐  │
│  │  ChatSidebar │     ChatArea      │      ChartPanel        │  │
│  │  (Sessions)  │ (Results + AI)    │   (SQL + Charts)       │  │
│  └──────────────┴───────────────────┴────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SSE (POST /api/chat)
┌──────────────────────────▼──────────────────────────────────────┐
│                       Backend (FastAPI)                          │
│  ┌────────────┐ ┌──────────────┐ ┌────────────┐ ┌───────────┐  │
│  │ Session API │ │  LLM Service │ │ DB Service │ │Chart Svc  │  │
│  │  (CRUD)     │ │ (LangChain)  │ │ (SQLite)   │ │(ECharts)  │  │
│  └────────────┘ └──────┬───────┘ └────────────┘ └───────────┘  │
└─────────────────────────┼───────────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │  Alibaba Cloud Qwen3  │
              │  (DashScope API)      │
              └───────────────────────┘
```

## Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| FastAPI | Web framework with async support |
| LangChain | LLM orchestration (NL→SQL chain, streaming) |
| ChatTongyi (Qwen3-max) | Alibaba Cloud LLM via DashScope API |
| SQLAlchemy | Async ORM for session/message persistence |
| SQLite | Application DB + sample business DB |
| SSE-Starlette | Server-Sent Events for streaming responses |

### Frontend

| Technology | Purpose |
|---|---|
| React 19 + TypeScript | UI framework |
| Vite 7 | Build tool with HMR |
| Ant Design 6 | UI component library |
| ECharts | Data visualization |
| Zustand | Lightweight state management |
| React Markdown | AI response rendering |

## Project Structure

```
NL2SQLAgent/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry, CORS, lifespan
│   │   ├── config.py               # Settings (.env, DB paths, model config)
│   │   ├── api/
│   │   │   ├── chat.py             # SSE chat endpoint
│   │   │   ├── sessions.py         # Session CRUD routes
│   │   │   └── database.py         # DB schema info route
│   │   ├── services/
│   │   │   ├── llm_service.py      # LangChain + Qwen3 (NL→SQL, streaming)
│   │   │   ├── db_service.py       # SQL execution sandbox, schema introspection
│   │   │   ├── session_service.py  # Session/message persistence
│   │   │   └── chart_service.py    # LLM-driven chart config generation
│   │   ├── models/
│   │   │   ├── database.py         # SQLAlchemy models (Session, Message)
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   └── prompts/
│   │       ├── text_to_sql.py      # NL→SQL prompt template
│   │       └── chart_gen.py        # Chart generation prompt template
│   ├── data/
│   │   ├── app.db                  # System DB (sessions, messages)
│   │   └── sample.db               # Sample business DB
│   ├── init_sample_db.py           # Sample data seeder
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Root layout (3-column)
│   │   ├── components/
│   │   │   ├── ChatSidebar/        # Left: session management
│   │   │   ├── ChatArea/           # Center: chat + results + AI analysis
│   │   │   └── ChartPanel/         # Right: SQL display + charts
│   │   ├── services/api.ts         # API client + SSE handler
│   │   ├── store/index.ts          # Zustand global state
│   │   └── types/index.ts          # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
```

## Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **Alibaba Cloud DashScope API Key** ([Get one here](https://dashscope.console.aliyun.com/))

### 1. Clone the Repository

```bash
git clone https://github.com/kennethwang412-svg/data-agent.git
cd data-agent
```

### 2. Backend Setup

```bash
cd NL2SQLAgent/backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your DashScope API key:
# DASHSCOPE_API_KEY=your_key_here

# Initialize sample database
python init_sample_db.py

# Start the server
python -m uvicorn app.main:app --reload --port 8001
```

The backend will be running at `http://127.0.0.1:8001`. Visit `/docs` for the Swagger UI.

### 3. Frontend Setup

```bash
cd NL2SQLAgent/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be running at `http://localhost:5173/`.

### 4. Use the Application

1. Open `http://localhost:5173/` in your browser
2. Click **"+ 新对话"** to create a new session
3. Type a question in Chinese, for example:
   - `各地区的销售总额是多少？`
   - `哪个产品类别最畅销？`
   - `2025年每月的销售趋势如何？`
4. Watch the real-time processing: SQL generation → execution → AI analysis → chart rendering

## Sample Database

The sample SQLite database (`sample.db`) contains mock business data for demonstration:

| Table | Description | Records |
|---|---|---|
| `products` | Product catalog (name, category, price) | 20 |
| `customers` | Customer profiles (name, region, level) | 50 |
| `orders` | Order records (customer, product, quantity, amount, date) | 200 |

**Example queries you can try:**

- "各地区的销售总额是多少？" — Sales by region
- "哪个地区的客户消费能力最强？" — Top spending region
- "每个月的销售额趋势" — Monthly sales trend
- "钻石客户和普通客户的平均消费对比" — VIP vs regular customer comparison
- "销量最高的前5个产品" — Top 5 products by sales volume

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/sessions` | Create a new session |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session detail with messages |
| `DELETE` | `/api/sessions/{id}` | Delete a session |
| `POST` | `/api/chat/{session_id}` | Send message, returns SSE stream |
| `GET` | `/api/database/tables` | Get database schema info |

### SSE Event Types

The chat endpoint streams the following events:

| Event | Description |
|---|---|
| `sql` | Generated SQL query |
| `query_result` | Query execution result (JSON) |
| `answer` | AI analysis text (streamed token by token) |
| `chart` | ECharts configuration (JSON) |
| `error` | Error message |
| `done` | Stream complete |

## License

MIT
