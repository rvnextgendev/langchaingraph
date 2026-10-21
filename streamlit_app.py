"""Launch with: python -m streamlit run streamlit_app.py."""

import logging

import streamlit as st

from order_assistant.service import answer_request

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Order assistant", page_icon="📦", layout="centered")
st.title("📦 Order assistant")
st.write("Check your order status with a simple workflow or a Groq assistant.")

labels = {
    "Workflow · no API key": "graph",
    "Groq agent": "agent",
    "Workflow + Groq reply": "hybrid",
    "Policy Q&A · RAG": "rag",
}
with st.sidebar:
    st.header("Assistant settings")
    selected = st.selectbox("Mode", list(labels))
    st.caption("Demo orders: 1001 — Shipped · 1002 — Processing")
    st.caption("Groq modes use GROQ_API_KEY and LLM_MODEL from your .env or environment.")
    st.caption("Each submission is independent. This demo has no conversation memory.")
    if st.button("Clear results", key="clear_results"):
        st.session_state.pop("order_result", None)

mode = labels[selected]
if mode == "rag":
    st.info("Ask about returns, refunds, shipping, or tracking. Policies are fictional demo data.")
elif mode == "agent":
    st.info("Ask a question such as: What is the status of order 1001?")
else:
    st.info("Enter an order ID, or leave it empty to see the missing-ID response.")

with st.form("order_request"):
    if mode in {"agent", "rag"}:
        request = st.text_area("Your question", max_chars=2000, key=f"{mode}_question")
    else:
        request = st.text_input("Order ID", max_chars=32, key="workflow_order_id")
    submitted = st.form_submit_button("Check status", type="primary", key="check_status")

if submitted:
    st.session_state.pop("order_result", None)
    try:
        with st.spinner("Checking your order…"):
            reply = answer_request(mode, request)
        st.session_state.order_result = {"mode": mode, "reply": reply}
    except ValueError as exc:
        st.error(str(exc))
    except ImportError:
        st.error('Install the UI dependencies with: python -m pip install -e ".[ui]"')
    except Exception as exc:
        logger.warning("Order request failed (%s)", type(exc).__name__)
        st.error("Unable to complete the request. Check Groq access, model, quota, and connection.")

result = st.session_state.get("order_result")
if result and result["mode"] == mode:
    st.subheader("Policy answer" if mode == "rag" else "Order update")
    st.write(result["reply"])
