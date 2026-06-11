# agent_executor.py
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    UnsupportedOperationError,
)
from a2a.utils import new_text_artifact  # ← fix nama function
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import root_agent


class ReservationAgentExecutor(AgentExecutor):
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=root_agent,
            app_name="reservation_agent",
            session_service=self.session_service,
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id,
                status=TaskStatus(state=TaskState.working),
                final=False,
            )
        )

        # Get or create session
        session = await self.session_service.get_session(
            app_name="reservation_agent",
            user_id=context.context_id,
            session_id=context.context_id,
        )
        if not session:
            session = await self.session_service.create_session(
                app_name="reservation_agent",
                user_id=context.context_id,
                session_id=context.context_id,
            )

        # Extract text from A2A message
        user_message = ""
        for part in context.message.parts:
            if hasattr(part.root, "text"):
                user_message += part.root.text

        response_text = ""
        async for event in self.runner.run_async(
            user_id=context.context_id,
            session_id=context.context_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_message)],
            ),
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id,
                artifact=new_text_artifact(
                    name="response",
                    text=response_text,
                    ),  # ← fix
            )
        )

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id,
                status=TaskStatus(state=TaskState.completed), 
                final=True,
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError("Cancellation not supported.")