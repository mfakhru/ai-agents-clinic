# scripts/test_a2a_agent_local.py
import asyncio
import json
import os
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("AGENT_URL", "http://localhost:8000")


def make_message(text: str, context_id: str = None, task_id: str = None) -> dict:
    msg = {
        "role": "user",
        "parts": [{"kind": "text", "text": text}],
        "messageId": str(uuid.uuid4()),
    }
    if context_id:
        msg["contextId"] = context_id
    if task_id:
        msg["taskId"] = task_id
    return msg


def make_request(text: str, context_id: str = None, task_id: str = None) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": str(uuid.uuid4()),
        "params": {
            "message": make_message(text, context_id, task_id),
        },
    }


def print_response(label: str, response: dict):
    print(f"\n{'=' * 50}")
    print(f"{label}")
    print(f"{'=' * 50}")
    result = response.get("result", {})
    status = result.get("status", {}).get("state", "unknown")
    print(f"Status: {status}")
    for artifact in result.get("artifacts", []):
        for part in artifact.get("parts", []):
            if "text" in part:
                print(f"Answer: {part['text']}")


async def send_message(client: httpx.AsyncClient, text: str, context_id: str = None) -> dict:
    payload = make_request(text, context_id)
    response = await client.post(BASE_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    # print(json.dumps(data, indent=2))  # ← tambah baris ini
    return data


async def get_agent_card(client: httpx.AsyncClient) -> dict:
    response = await client.get(f"{BASE_URL}/.well-known/agent.json")
    response.raise_for_status()
    return response.json()


async def main():
    async with httpx.AsyncClient(timeout=30) as client:

        # 1. Get agent card
        print("=" * 50)
        print("1. Retrieving agent card...")
        print("=" * 50)
        card = await get_agent_card(client)
        print(f"Agent   : {card.get('name')}")
        print(f"Version : {card.get('version')}")
        print(f"Skills  : {[s.get('name') for s in card.get('skills', [])]}")

        # 2. Create a reservation
        response = await send_message(
            client,
            "I want to book an appointment. "
            "Name: Budi, Phone: 08123456789, "
            "Service: Scaling & Polishing, "
            "Date: 2025-07-15, Time: 10:00 AM",
        )
        print_response("2. Creating a reservation...", response)
        context_id = response.get("result", {}).get("contextId")

        # 2b. Confirm the reservation  ← tambah ini
        response = await send_message(
            client,
            "Yes, please confirm the booking.",
            context_id=context_id,
        )
        print_response("2b. Confirming reservation...", response)

        # 3. Check the reservation
        response = await send_message(
            client,
            "Check my appointment for 08123456789",
            context_id=context_id,
        )
        print_response("3. Checking the reservation...", response)

        # 4. Cancel the reservation
        response = await send_message(
            client,
            "Cancel my appointment for 08123456789",
            context_id=context_id,
        )
        print_response("4. Cancelling the reservation...", response)

        # 5. Check again after cancel
        response = await send_message(
            client,
            "Check my appointment for 08123456789",
            context_id=context_id,
        )
        print_response("5. Check after cancel...", response)

        print(f"\n{'=' * 50}")
        print("All tests done!")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())