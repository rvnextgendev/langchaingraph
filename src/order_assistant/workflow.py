"""Explicit branching: inspect -> lookup -> reply, or inspect -> ask."""

import logging
from collections.abc import Callable
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from order_assistant.orders import OrderRepository, lookup_status, normalize_order_id

logger = logging.getLogger(__name__)
ReplyWriter = Callable[[str, str], str]


class OrderState(TypedDict, total=False):
    order_id: str
    status: str
    reply: str


def format_reply(order_id: str, status: str) -> str:
    return f"Order {order_id}: {status}"


def build_workflow(
    repository: OrderRepository, reply_writer: ReplyWriter = format_reply
) -> CompiledStateGraph:
    """Inject dependencies so nodes need no global model or database connection."""

    def inspect_request(state: OrderState) -> OrderState:
        return {"order_id": normalize_order_id(state.get("order_id", ""))}

    def choose_path(state: OrderState) -> Literal["lookup", "ask"]:
        return "lookup" if state["order_id"] else "ask"

    def lookup_order(state: OrderState) -> OrderState:
        logger.debug("Looking up order status")
        return {"status": lookup_status(repository, state["order_id"])}

    def write_reply(state: OrderState) -> OrderState:
        return {"reply": reply_writer(state["order_id"], state["status"])}

    def ask_for_id(state: OrderState) -> OrderState:
        return {"reply": "Please provide your order ID."}

    builder = StateGraph(OrderState)
    builder.add_node("inspect", inspect_request)
    builder.add_node("lookup", lookup_order)
    builder.add_node("reply", write_reply)
    builder.add_node("ask", ask_for_id)
    builder.add_edge(START, "inspect")
    builder.add_conditional_edges("inspect", choose_path, {"lookup": "lookup", "ask": "ask"})
    builder.add_edge("lookup", "reply")
    builder.add_edge("reply", END)
    builder.add_edge("ask", END)
    return builder.compile()
