from pathlib import Path
from unittest.mock import patch

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def test_workflow_ui_and_clear_results():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    app.text_input[0].set_value("1001")
    app.button(key="check_status").click().run()
    assert not app.exception
    assert any(item.value == "Order 1001: Shipped" for item in app.markdown)
    app.button(key="clear_results").click().run()
    assert not any(item.value == "Order 1001: Shipped" for item in app.markdown)


def test_agent_ui_shows_safe_provider_error():
    app = AppTest.from_file(str(APP)).run()
    app.selectbox[0].select("Groq agent").run()
    app.text_area[0].set_value("Where is order 1001?")
    with patch("order_assistant.service.answer_request", side_effect=RuntimeError("secret")):
        app.button(key="check_status").click().run()
    assert not app.exception
    assert "Unable to complete" in app.error[0].value
    assert "secret" not in app.error[0].value


def test_policy_rag_ui_displays_sources():
    app = AppTest.from_file(str(APP)).run()
    app.selectbox[0].select("Policy Q&A · RAG").run()
    app.text_area[0].set_value("What is the return policy?")
    with (
        patch("order_assistant.llm.Settings.from_env"),
        patch("order_assistant.llm.build_model") as model,
    ):
        model.return_value.invoke.return_value.text = "Return within 30 days of delivery. [1]"
        app.button(key="check_status").click().run()
    assert not app.exception
    assert any("returns.md" in item.value for item in app.markdown)
