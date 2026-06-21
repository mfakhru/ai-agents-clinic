# AI Dental Clinic Assistant (Bright Smile Dental Clinic)

An intelligent, conversational AI receptionist agent designed to assist patients at "Bright Smile Dental Clinic." This project demonstrates a **multi-agent architecture** using the **Google ADK (Agent Development Kit)** and the **A2A (Agent-to-Agent) protocol**.

## Features

- **Service Discovery:** Browse dental services by category (Preventive, Cosmetic, etc.) or appointment type.
- **Semantic Search:** Patients can describe symptoms or dental goals in natural language to find the most relevant treatments.
- **Detailed Service Info:** Provides complete details including pricing, duration, and insurance eligibility.
- **Service Management:** Integrated tools to add or update clinic services dynamically.
- **Appointment Management:** Patients can book, check, and cancel dental appointments using their phone number as an identifier.
- **Telegram Integration:** Chat with the agent directly from Telegram.

## Tech Stack

- **Core Framework:** [Google ADK](https://pypi.org/project/google-adk/)
- **Inter-Agent Protocol:** [A2A SDK](https://pypi.org/project/a2a-sdk/)
- **LLM:** Google Gemini 3 Flash Preview
- **Language:** Python 3.12+
- **Database:** SQLite (local)
- **Tool Server:** [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox-for-databases)

## Architecture

```
User / Telegram
     │
     ▼
┌─────────────────────────────────┐
│  clinic_agent  (ADK Web / API)  │  ← root agent, port 8000
│  - search-services              │
│  - get-service-details          │
│  - search-services-by-description│
│  - add-service                  │
└──────────────┬──────────────────┘
               │ A2A (RemoteA2aAgent)
               ▼
┌──────────────────────────────────┐
│  reservation_agent  (A2A Server) │  ← sub-agent, port 8001
│  - create_reservation            │
│  - check_reservation             │
│  - cancel_reservation            │
└──────────────────────────────────┘
               │
               ▼
       SQLite (database/clinic.db)
       via MCP Toolbox (port 5000)
```

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management
- A Google API Key with Gemini access ([get one here](https://aistudio.google.com/app/apikey))
- Telegram Bot Token (optional, for Telegram integration)

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/mfakhru/ai-agents-clinic.git
cd ai-agents-clinic
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Download the Toolbox binary

```bash
curl -O https://storage.googleapis.com/mcp-toolbox-for-databases/v1.1.0/linux/amd64/toolbox
chmod +x toolbox
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials (at minimum, `GOOGLE_API_KEY` and `DB_PATH` are required).

### 5. Create the logs directory

```bash
mkdir -p logs
```

### 6. Initialize the database

Seeds 20 dental services and generates semantic embeddings:

```bash
uv run python scripts/setup_data.py
```

## Running the Project

You need **three terminal windows** running at the same time.

### Terminal 1 — MCP Toolbox (database tool server)

```bash
set -a; source .env; set +a
./toolbox --config tools.yaml --enable-api > logs/mcp_toolbox.log 2>&1 &
```

Verify it's running:
```bash
curl http://localhost:5000/api/toolset/my-toolset
```

### Terminal 2 — Reservation Agent (A2A server, port 8001)

```bash
cd reservation_agent
uv run python __main__.py
```

Verify it's running:
```bash
curl http://localhost:8001/.well-known/agent.json
```

### Terminal 3 — Clinic Agent (ADK Web UI, port 8000)

```bash
uv run adk web
```

Open [http://localhost:8000](http://localhost:8000) in your browser and select `clinic_agent` to start chatting.

## Telegram Integration (Optional)

Once the clinic agent is running, start the Telegram bot in a separate terminal:

```bash
cd telegram-integration
pip install -r requirements.txt
python main.py
```

The bot will run in **polling mode** by default. To use **webhook mode** (e.g., on Cloud Run), set `PORT` and `SERVICE_URL` in your `.env`.

## Testing

### Test clinic agent directly (no ADK Web)

```bash
uv run python scripts/test_invoke.py
```

### Test reservation agent via A2A protocol

```bash
uv run python scripts/test_a2a_agent_local.py
```

## Project Structure

```
ai-agents-clinic/
├── clinic_agent/               # Root agent (service discovery + orchestration)
│   ├── __init__.py
│   └── agent.py
├── reservation_agent/          # Appointment sub-agent (A2A server)
│   ├── __init__.py
│   ├── __main__.py             # Uvicorn entry point (port 8001)
│   ├── agent.py                # Agent + reservation tools
│   └── agent_executor.py       # A2A executor
├── telegram-integration/       # Telegram bot frontend
│   ├── main.py
│   └── requirements.txt
├── scripts/
│   ├── setup_data.py           # DB seed + embedding generation
│   ├── test_invoke.py          # Test clinic_agent directly
│   ├── test_a2a_agent_local.py # Test reservation_agent via A2A
│   └── verify_seed.py          # Verify DB seed
├── database/
│   └── clinic.db               # SQLite database (auto-created)
├── logs/                       # Log files (auto-created)
├── tools.yaml                  # MCP Toolbox tool definitions
├── toolbox                     # MCP Toolbox binary (download separately)
├── .env.example                # Environment variable template
└── pyproject.toml
```

## Example Conversations

**Browsing services:**
> "What cosmetic services do you offer?"

**Semantic search:**
> "My teeth are very sensitive to cold, what treatment do I need?"

**Booking an appointment:**
> "I'd like to book a teeth whitening for next Monday at 2 PM. My name is Budi and my number is 08123456789."

**Checking an appointment:**
> "Can you check my appointment? My number is 08123456789."
