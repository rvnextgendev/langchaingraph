from unittest.mock import Mock

import pytest

from order_assistant.orders import demo_repository
from order_assistant.workflow import build_workflow


@pytest.mark.parametrize(
    ("order_id", "expected"),
    [
        ("1001", "Order 1001: Shipped"),
        (" 1002 ", "Order 1002: Processing"),
        ("9999", "Order 9999: Order not found"),
        ("", "Please provide your order ID."),
        ("   ", "Please provide your order ID."),
    ],
)
def test_workflow_routes(order_id, expected):
    graph = build_workflow(demo_repository())
    assert graph.invoke({"order_id": order_id})["reply"] == expected


def test_missing_id_skips_repository_and_writer():
    repository, writer = Mock(), Mock()
    graph = build_workflow(repository, writer)
    assert graph.invoke({})["reply"] == "Please provide your order ID."
    repository.get_status.assert_not_called()
    writer.assert_not_called()


@pytest.mark.parametrize("value", ["abc", "1; DROP TABLE orders", "1" * 33, 1001, None])
def test_invalid_id_is_rejected_before_lookup(value):
    repository = Mock()
    with pytest.raises(ValueError):
        build_workflow(repository).invoke({"order_id": value})
    repository.get_status.assert_not_called()


def test_reply_writer_receives_repository_facts():
    writer = Mock(return_value="Your order has shipped.")
    result = build_workflow(demo_repository(), writer).invoke({"order_id": "1001"})
    assert result["reply"] == "Your order has shipped."
    writer.assert_called_once_with("1001", "Shipped")
