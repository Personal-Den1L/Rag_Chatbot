import chainlit as cl
import os

# Fetch the API URL from the environment variables (set in docker-compose.yml)
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@cl.on_chat_start
async def on_chat_start():
    """
    Fires when a user opens the chat interface.
    """
    await cl.Message(
        content="Welcome to the DA-IICT Assistant! The UI is connected, but the backend AI is still under construction."
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """
    Fires whenever the user sends a message.
    """
    # For now, we just echo back a hardcoded response.
    # Later, we will use the 'requests' library here to POST the message to our FastAPI backend.
    
    await cl.Message(
        content=f"You said: '{message.content}'. \n\n(API is located at {API_URL}, but integration is pending.)"
    ).send()