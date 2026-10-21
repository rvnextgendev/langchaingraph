"""Shared request handling for CLI and Streamlit interfaces."""

from typing import Literal

from order_assistant.orders import demo_repository
from order_assistant.workflow import build_workflow, format_reply

Mode = Literal["graph", "agent", "hybrid", "rag"]


def answer_request(mode: Mode, request: str) -> str:
    """Handle one independent request; construct models only for Groq modes."""
    if mode not in {"graph", "agent", "hybrid", "rag"}:
        raise ValueError("Choose graph, agent, hybrid, or rag mode.")
    if not isinstance(request, str) or len(request) > 2000:
        raise ValueError("Request must be text of at most 2000 characters.")
    if mode == "rag":
        from order_assistant.rag_workflow import build_rag_workflow

        def model_factory():
            from order_assistant.llm import Settings, build_model

            return build_model(Settings.from_env())

        return build_rag_workflow(model_factory).invoke(
            {"question": request}, {"recursion_limit": 10}
        )["reply"]
    repository = demo_repository()
    writer = format_reply
    if mode in {"agent", "hybrid"}:
        from order_assistant.llm import Settings, build_agent, build_model, build_reply_writer

        if mode == "agent" and not request.strip():
            raise ValueError("Enter a question.")
        model = build_model(Settings.from_env())
        if mode == "agent":
            result = build_agent(model, repository).invoke(
                {"messages": [{"role": "user", "content": request}]},
                {"recursion_limit": 10},
            )
            final = result["messages"][-1]
            if final.type != "ai" or final.tool_calls or not final.text.strip():
                raise RuntimeError("Agent did not return a final answer.")
            return final.text.strip()
        writer = build_reply_writer(model)
    result = build_workflow(repository, writer).invoke(
        {"order_id": request}, {"recursion_limit": 10}
    )
    return result["reply"]
