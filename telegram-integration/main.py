# ./telegram-integration/main.py

import asyncio
import os
import re
import sys
import httpx
from html import escape

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from dotenv import load_dotenv

load_dotenv()

# Read token from environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADK_SERVER_URL = os.environ.get("ADK_SERVER_URL", "http://localhost:8000")
ADK_APP_NAME = os.environ.get("ADK_APP_NAME", "clinic_agent")

# Parse base URL out of ADK_SERVER_URL
BASE_URL = ADK_SERVER_URL.rstrip('/')
if BASE_URL.endswith('/run'):
    BASE_URL = BASE_URL[:-4]
elif BASE_URL.endswith('/query'):
    BASE_URL = BASE_URL[:-6]

if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    print("Please set it before running the application.")
    sys.exit(1)

def md_to_html(text: str) -> str:
    """Convert basic markdown to Telegram HTML (bold, italic, code, headers)."""
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'_([^_\n]+)_', r'<i>\1</i>', text)
    text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
    text = re.sub(r'^#{1,6}\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    return text


async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I am your ADK Integration Bot. Send me a message and I will forward it to the ADK server.')

async def send_typing_loop(chat_id: int, bot, stop_event: asyncio.Event):
    """Send typing action periodically until the stop event is set."""
    while not stop_event.is_set():
        try:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            # The research suggested repeating every 4 seconds
            await asyncio.sleep(4)
        except Exception as e:
            print(f"Error sending chat action: {e}")
            await asyncio.sleep(1) # Wait a bit before retrying if error

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming user messages."""
    user_message = update.message.text
    chat_id = update.message.chat_id
    raw_user_id = str(update.message.from_user.id)
    
    # Derive unique user_id and session_id for this user
    user_id = f"tg_{raw_user_id}"
    session_id = f"tg_sess_{raw_user_id}"

    print(f"Received message from {user_id}: {user_message}")

    # Create a stop event for the typing loop
    stop_event = asyncio.Event()
    
    # Start the typing loop as a background task
    typing_task = asyncio.create_task(send_typing_loop(chat_id, context.bot, stop_event))

    try:
        async with httpx.AsyncClient() as client:
            # 1. Check if the session exists
            session_url = f"{BASE_URL}/apps/{ADK_APP_NAME}/users/{user_id}/sessions/{session_id}"
            session_check = await client.get(session_url, timeout=10.0)
            
            if session_check.status_code == 404:
                # 2. If session doesn't exist, create it
                print(f"Session {session_id} not found. Creating session...")
                session_create = await client.post(session_url, json={}, timeout=10.0)
                if session_create.status_code != 200:
                    raise Exception(f"Failed to create session: {session_create.status_code} {session_create.text}")
            elif session_check.status_code != 200:
                raise Exception(f"Error checking session: {session_check.status_code} {session_check.text}")
            
            # 3. Run the ADK agent
            run_url = f"{BASE_URL}/run"
            payload = {
                "appName": ADK_APP_NAME,
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": user_message}]
                }
            }
            response = await client.post(run_url, json=payload, timeout=60.0)
            
        if response.status_code == 200:
            events = response.json()
            if isinstance(events, list) and len(events) > 0:
                # The last event contains the final text response
                last_event = events[-1]
                content = last_event.get("content", {})
                parts = content.get("parts", [])
                if parts and "text" in parts[0]:
                    reply_text = parts[0]["text"]
                else:
                    reply_text = "ADK agent returned an empty or non-text response."
            else:
                reply_text = "No events returned from ADK agent."
        else:
            reply_text = f"Error communicating with ADK server (Status: {response.status_code})."
            
    except Exception as e:
        reply_text = f"Failed to connect to ADK server: {e}"
    finally:
        # Stop the typing loop
        stop_event.set()
        await typing_task

    # Send the final response back to the user
    await update.message.reply_text(md_to_html(reply_text), parse_mode='HTML')

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Check if running in webhook mode (e.g., on Cloud Run)
    port = os.environ.get("PORT")
    service_url = os.environ.get("SERVICE_URL")

    if port and service_url:
        if not service_url.startswith("http"):
            service_url = f"https://{service_url}"
        
        print(f"Starting bot in WEBHOOK mode on port {port} with url {service_url}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=int(port),
            url_path=TOKEN,
            webhook_url=f"{service_url}/{TOKEN}",
            allowed_updates=Update.ALL_TYPES
        )
    else:
        print("Starting bot in POLLING mode")
        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()