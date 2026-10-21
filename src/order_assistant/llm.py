"""Optional model configuration, agent construction, and hybrid reply writing."""

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from order_assistant.orders import OrderRepository, lookup_status
from order_assistant.workflow import ReplyWriter, format_reply

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    model: str
    api_key: str = field(repr=False)

    @classmethod
    def from_env(cls) -> "Settings":
        from dotenv import load_dotenv

        load_dotenv()
        provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
        if provider != "groq":
            raise ValueError("Only LLM_PROVIDER=groq is supported.")
        model = os.getenv("LLM_MODEL", "").strip() or os.getenv("GROQ_MODEL", "").strip()
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not model or not api_key:
            raise ValueError(
                "Set LLM_MODEL (or GROQ_MODEL) and GROQ_API_KEY in your environment or .env."
            )
        return cls(model=model, api_key=api_key)


def build_model(settings: Settings) -> Any:
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.model,
        api_key=settings.api_key,
        temperature=0,
        max_tokens=1024,
        timeout=30,
        max_retries=2,
    )


def build_agent(model: Any, repository: OrderRepository) -> Any:
    from langchain.agents import create_agent

    def get_order_status(order_id: str) -> str:
        """Look up an order status using its numeric order ID."""
        try:
            return lookup_status(repository, order_id)
        except ValueError as exc:
            return str(exc)

    return create_agent(
        model=model,
        tools=[get_order_status],
        system_prompt=(
            "You are an order support assistant. Use get_order_status for order status "
            "questions. Ask for the order ID if missing. Never invent an order status."
        ),
    )


def build_reply_writer(model: Any) -> ReplyWriter:
    """Use model wording; preserve the factual reply if the model is unavailable."""

    def write_reply(order_id: str, status: str) -> str:
        try:
            response = model.invoke(
                [
                    (
                        "system",
                        "Write one short order status reply using only the supplied facts. "
                        "Do not invent dates or promises.",
                    ),
                    ("human", f"Order ID: {order_id}\nStatus: {status}"),
                ]
            )
            if response.text.strip():
                return response.text.strip()
        except Exception as exc:
            logger.warning("Model reply unavailable (%s); using template", type(exc).__name__)
        return format_reply(order_id, status)

    return write_reply
