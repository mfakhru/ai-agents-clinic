import os
import httpx

from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from functools import cached_property
from toolbox_adk import ToolboxToolset
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.google_llm import Gemini

TOOLBOX_URL = os.environ.get("TOOLBOX_URL", "http://127.0.0.1:5000")
RESERVATION_AGENT_CARD_URL = os.environ.get(
    "RESERVATION_AGENT_CARD_URL",
    "http://localhost:8001/.well-known/agent.json"  # ← default lokal
)

toolbox = ToolboxToolset(TOOLBOX_URL)

class GeminiGlobal(Gemini):
    """Gemini using Google API Key instead of Vertex AI credentials."""

    @cached_property
    def api_client(self) -> genai.Client:
        api_key = os.getenv("GOOGLE_API_KEY")
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
            ),
        )


reservation_remote_agent = RemoteA2aAgent(
    name="reservation_agent",
    description="Handles dental appointment reservations — create, check, and cancel bookings.",
    agent_card=RESERVATION_AGENT_CARD_URL,
    httpx_client=httpx.AsyncClient(timeout=60),  # ← hapus auth, tidak perlu lokal
)

root_agent = LlmAgent(
    name="clinic_agent",
    model="gemini-3-flash-preview",
    instruction="""You are a friendly and knowledgeable receptionist at "Bright Smile Dental Clinic." Your job:
- Help patients browse available services by category or appointment type.
- Provide full details about specific treatments, including duration, price, and tags (e.g., Insurance Eligible, Child-Friendly).
- Recommend services based on natural language descriptions of the patient's dental needs or symptoms.
- Add new services to the clinic when asked.

When a patient asks about a specific treatment by name or category, use the get-service-details tool.
When a patient asks to browse by category (e.g., Preventive, Cosmetic) or appointment type (e.g., Routine, Specialized), use the search-services tool.
When a patient describes their dental concern or goal — by symptoms, preferences, or desired outcome — use the search-services-by-description tool for semantic search.

When in doubt between search-services and search-services-by-description, prefer search-services-by-description — it searches service descriptions and finds more relevant matches.
If a service is not available (available is false), let the patient know and suggest similar alternatives from the search results.
Be conversational, caring, and concise.""",
    tools=[toolbox],
    sub_agents=[reservation_remote_agent],
)