from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import AIMessage

from order_assistant.service import answer_request


def test_graph_mode_does_not_build_a_model():
    with patch("order_assistant.llm.build_model") as model:
        assert answer_request("graph", "1001") == "Order 1001: Shipped"
    model.assert_not_called()


def test_agent_uses_groq_factory_and_returns_final_text():
    agent = Mock()
    agent.invoke.return_value = {"messages": [AIMessage(content="Order 1001 is shipped.")]}
    with (
        patch("order_assistant.llm.Settings.from_env"),
        patch("order_assistant.llm.build_model"),
        patch("order_assistant.llm.build_agent", return_value=agent),
    ):
        assert answer_request("agent", "Where is order 1001?") == "Order 1001 is shipped."


@pytest.mark.parametrize("question", ["", " ", "x" * 2001])
def test_agent_rejects_invalid_requests(question):
    with pytest.raises(ValueError):
        answer_request("agent", question)
