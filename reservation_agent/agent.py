# reservation_agent/agent.py
import os
from functools import cached_property
from typing import Any

from google import genai
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import ToolContext
from google.genai import Client, types

# App-scoped state prefix ensures reservations persist across all sessions.
# See https://adk.dev/sessions/state/ for state scope details.
STATE_PREFIX = "app:reservation:"



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


def create_reservation(
    phone_number: str,
    name: str,
    service: str,
    date: str,
    time: str,
    tool_context: ToolContext,
) -> dict:
    """Create a new dental appointment reservation.

    Args:
        phone_number: Patient's phone number, used as the reservation ID.
        name: Name for the reservation.
        service: Dental service requested (e.g., 'Scaling & Polishing', 'Root Canal Treatment').
        date: Appointment date (e.g., '2025-07-15' or 'this Friday').
        time: Appointment time (e.g., '10:00 AM').

    Returns:
        Confirmation of the appointment.
    """
    reservation = {
        "name": name,
        "service": service,
        "date": date,
        "time": time,
        "status": "confirmed",
    }
    tool_context.state[f"{STATE_PREFIX}{phone_number}"] = reservation
    return {
        "status": "confirmed",
        "message": f"Appointment confirmed for {name} — {service} on {date} at {time}. Phone: {phone_number}.",
    }


def check_reservation(phone_number: str, tool_context: ToolContext) -> dict:
    """Look up an existing appointment by phone number.

    Args:
        phone_number: The phone number used when the appointment was booked.
        tool_context: ADK tool context for state access.

    Returns:
        The appointment details, or a message if not found.
    """
    reservation = tool_context.state.get(f"{STATE_PREFIX}{phone_number}")
    if reservation:
        return {"found": True, "reservation": reservation}
    return {"found": False, "message": f"No appointment found for {phone_number}."}


def cancel_reservation(phone_number: str, tool_context: ToolContext) -> dict:
    """Cancel an existing appointment by phone number.

    Args:
        phone_number: The phone number used when the appointment was booked.
        tool_context: ADK tool context for state access.

    Returns:
        Confirmation of cancellation, or a message if not found.
    """
    key = f"{STATE_PREFIX}{phone_number}"
    reservation = tool_context.state.get(key)
    if not reservation:
        return {
            "success": False,
            "message": f"No appointment found for {phone_number}.",
        }
    if reservation.get("status") == "cancelled":
        return {
            "success": False,
            "message": f"Appointment for {phone_number} is already cancelled.",
        }
    reservation["status"] = "cancelled"
    tool_context.state[key] = reservation
    return {
        "success": True,
        "message": f"Appointment for {reservation['name']} ({phone_number}) — {reservation['service']} has been cancelled.",
    }


root_agent = LlmAgent(
    name="reservation_agent",
    model=GeminiGlobal(model="gemini-3-flash-preview"),
    instruction="""You are a friendly appointment assistant for "Bright Smile Dental Clinic."
You help patients book, check, and cancel dental appointments.

When a patient wants to make an appointment, collect these details:
- Name
- Phone number (used as the appointment ID)
- Dental service requested (e.g., Scaling & Polishing, Teeth Whitening, Root Canal Treatment)
- Date
- Time

Always confirm the details before creating the appointment.
When checking or cancelling, ask for the phone number if not provided.
Be concise, caring, and professional.""",
    tools=[create_reservation, check_reservation, cancel_reservation],
)
