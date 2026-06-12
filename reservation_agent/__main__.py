# __main__.py
import os
import asyncio
import uvicorn

from dotenv import load_dotenv
load_dotenv()

from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import ReservationAgentExecutor


def create_agent_card() -> AgentCard:
    return AgentCard(
        name="Bright Smile Dental Clinic Assistant",
        description=(
            "A friendly appointment assistant for Bright Smile Dental Clinic. "
            "Helps patients book, check, and cancel dental appointments."
        ),
        url=os.getenv("AGENT_URL", "http://localhost:8001"),
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="create_reservation",
                name="Book Appointment",
                description="Book a new dental appointment.",
                tags=["reservation", "booking"],  # ← tambah ini
                examples=[
                    "I want to book a scaling and polishing",
                    "Schedule root canal next Monday 10 AM",
                ],
            ),
            AgentSkill(
                id="check_reservation",
                name="Check Appointment",
                description="Check existing appointment by phone number.",
                tags=["reservation", "check"],  # ← tambah ini
                examples=["Check my appointment for 08123456789"],
            ),
            AgentSkill(
                id="cancel_reservation",
                name="Cancel Appointment",
                description="Cancel an existing appointment by phone number.",
                tags=["reservation", "cancel"],  # ← tambah ini
                examples=["Cancel my appointment for 08123456789"],
            ),
        ],
    )


async def main():
    handler = DefaultRequestHandler(
        agent_executor=ReservationAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=create_agent_card(),
        http_handler=handler,
    ).build()

    config = uvicorn.Config(
        app,
        host="0.0.0.0", 
        port=8001,
        headers=[("Access-Control-Allow-Origin", "*")]
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())