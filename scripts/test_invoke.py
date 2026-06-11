import asyncio
import os
import sys
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# ── Import your agent ─────────────────────────────────────────────────────────
# Adjust the import path to match your project structure
# e.g. if your agent is at clinic_agent/agent.py and exposes `root_agent`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clinic_agent.agent import root_agent
# from reservation_agent.agent import root_agent

# ── Constants ─────────────────────────────────────────────────────────────────
APP_NAME    = "clinic_agent"
# APP_NAME    = "reservation_agent"
USER_ID     = "user_001"
SESSION_ID  = "session_001"


async def invoke_agent(user_message: str) -> str:
    """Send a message to the agent and return its response."""

    # 1. Session service (in-memory for quick testing)
    session_service = InMemorySessionService()

    # 2. Create (or reuse) a session
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    # 3. Build the runner
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # 4. Wrap the user message
    message = types.Content(
        role="user",
        parts=[types.Part(text=user_message)],
    )

    # 5. Stream events and collect the final text response
    final_response = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message,
    ):
        # The last event with text content is the agent's reply
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            break

    return final_response


async def main():
    print("=== Agent Tester ===")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        response = await invoke_agent(user_input)
        print(f"Agent: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())