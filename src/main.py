"""FastAPI app entrypoint: wires up routers and startup tasks.

Message flow overview:
1. Customer sends a WhatsApp message -> Meta posts to POST /webhook (src/routes/webhook.py).
2. src/handlers/message_handler.py identifies the business, persists/loads conversation history.
3. src/services/llm_agent.py classifies intent via OpenAI.
4. src/handlers/intent_handler.py fetches real data via src/services/data_access.py (never the LLM)
   and sends the reply via src/services/whatsapp_client.py.
"""
import logging

from fastapi import FastAPI

from src.db import init_db
from src.routes import admin, health, webhook

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="WhatsApp AI Business Agent")


@app.on_event("startup")
async def on_startup():
    """Create the local SQLite tables if they don't exist yet."""
    await init_db()


app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(admin.router)
