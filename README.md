# AI Dental Clinic Assistant (Bright Smile Dental Clinic)

An intelligent, conversational AI receptionist agent designed to assist patients at "Bright Smile Dental Clinic." This agent is built using the **Google ADK (Agent Development Kit)**.

## 🚀 Features

- 🦷 **Service Discovery:** Easily browse dental services by category (Preventive, Cosmetic, etc.) or appointment type.
- 🔍 **Semantic Search:** Patients can describe symptoms or dental goals in natural language to find the most relevant treatments.
- 💰 **Detailed Service Info:** Provides complete details including pricing, duration, and insurance eligibility.
- 🛠️ **Service Management:** Integrated tools to add or update clinic services dynamically.
- 🤖 **Empathetic AI:** Designed to be conversational, caring, and professional.

## 🛠️ Tech Stack

- **Core Framework:** [Google ADK](https://pypi.org/project/google-adk/)
- **LLM:** Google Gemini (3 Flash Preview)
- **Language:** Python 3.12+
- **Database:** SQLite (local)
- **Tools:** Custom Toolbox Toolset

## 📋 Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)
- A Google Cloud Project with Gemini API access

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd ai-agents-clinic
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Download Toolbox:**
   The project requires the `toolbox` binary to interact with the database. Download it using:
   ```bash
   curl -O https://storage.googleapis.com/mcp-toolbox-for-databases/v1.1.0/linux/amd64/toolbox
   chmod +x toolbox
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GEMINI_API_KEY=your_api_key_here
   TOOLBOX_URL=http://127.0.0.1:5000
   ```

5. **Initialize Database (Optional):**
   ```bash
   python scripts/setup_data.py
   ```

## 🏃 Usage

### 1. Start the Toolbox (Backend)
The toolbox must be running for the agent to access the database:
```bash
# Export environment variables and run toolbox in background
set -a; source .env; set +a
./toolbox --config tools.yaml --enable-api > logs/mcp_toolbox.log 2>&1 &
```

### 2. Run the Agent
To start the main application:
```bash
python main.py
```

To test the agent's invocation:
```bash
python scripts/test_invoke.py
```

## 📂 Project Structure

- `clinic_agent/`: Contains the core agent definition and instructions.
- `database/`: Local storage for clinic data.
- `logs/`: Directory for log files.
- `scripts/`: Helper scripts for data seeding and testing.
- `tools.yaml`: Configuration for agent tools.
- `toolbox`: Binary for database interaction.
