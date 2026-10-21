"""Business logic shared by the agent and workflow."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


def normalize_order_id(value: str) -> str:
    """Allow missing IDs; reject malformed IDs before querying the repository."""
    if not isinstance(value, str):
        raise ValueError("Order ID must be text.")
    value = value.strip()
    if value and (len(value) > 32 or not value.isascii() or not value.isdigit()):
        raise ValueError("Order ID must contain 1 to 32 digits.")
    return value


class OrderRepository(Protocol):
    """Replace this boundary with an authorized database/API lookup when needed."""

    def get_status(self, order_id: str) -> str | None: ...


@dataclass(frozen=True)
class InMemoryOrderRepository:
    orders: Mapping[str, str]

    def get_status(self, order_id: str) -> str | None:
        return self.orders.get(order_id)


def demo_repository() -> InMemoryOrderRepository:
    return InMemoryOrderRepository({"1001": "Shipped", "1002": "Processing"})


def lookup_status(repository: OrderRepository, order_id: str) -> str:
    order_id = normalize_order_id(order_id)
    if not order_id:
        return "Please provide your order ID."
    return repository.get_status(order_id) or "Order not found"
