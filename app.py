import os, json
from pathlib import Path
import streamlit as st

# Automatically load .env file if present so credentials default in sidebar
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from monday_client import MondayClient, MondayAPIError
from agent import plan_query, answer_query, build_leadership_update

st.set_page_config(page_title="Skylark BI Agent", page_icon="📊", layout="wide")
st.title("📊 Skylark Drones — Monday.com BI Agent")
st.caption("Read-only business intelligence agent for Work Orders and Deals")

DEFAULT_MONDAY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjY5ODMyNTE2OCwiYWFpIjoxMSwidWlkIjoxMTQ3OTE4MjEsImlhZCI6IjIwMjYtMDgtMzBUMDc6NDQ6MTEuMzAwWiIsInBlciI6Im1lOndyaXRlIiwiYWN0aWQiOjM2NjcyMzI4LCJyZ24iOiJhcHNlMiJ9.k_nGTA6U3ORViqWgh_QW85S1_yj_sSAeqO_kIG1gr_Q"
DEFAULT_DEALS_BOARD_ID = "5030967600"
DEFAULT_WORK_ORDERS_BOARD_ID = "5030967610"
DEFAULT_NVIDIA_API_KEY = "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"
DEFAULT_NVIDIA_MODEL = "deepseek-ai/deepseek-v4-pro-0813"

with st.sidebar:
    with st.expander("⚙️ Connection Settings", expanded=False):
        monday_token = st.text_input(
            "Monday API token",
            value=os.getenv("MONDAY_API_TOKEN", DEFAULT_MONDAY_TOKEN),
            type="password",
            help="Use a Monday.com token with boards:read permission."
        )
        deals_board = st.text_input("Deals board ID", value=os.getenv("DEALS_BOARD_ID", DEFAULT_DEALS_BOARD_ID))
        work_orders_board = st.text_input("Work Orders board ID", value=os.getenv("WORK_ORDERS_BOARD_ID", DEFAULT_WORK_ORDERS_BOARD_ID))
        nvidia_key = st.text_input(
            "NVIDIA API key",
            value=os.getenv("NVIDIA_API_KEY", DEFAULT_NVIDIA_API_KEY),
            type="password",
            help="NVIDIA NIM API key from integrate.api.nvidia.com. Required for AI-powered answers."
        )
        model = st.text_input("NVIDIA model", value=os.getenv("NVIDIA_MODEL", DEFAULT_NVIDIA_MODEL))

    st.divider()
    st.markdown("**Read-only by design:** this prototype only calls Monday GraphQL queries.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "plan" in m:
            with st.expander("Query plan / data quality"):
                st.json(m["plan"])

query = st.chat_input("Ask a founder-level question, e.g. How is the energy pipeline this quarter?")

if query:
    # Append & render user question immediately
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    if not monday_token or not deals_board or not work_orders_board:
        msg = "Please enter the Monday API token and both board IDs in the sidebar."
        with st.chat_message("assistant"):
            st.warning(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})
    else:
        with st.chat_message("assistant"):
            with st.status("Analyzing your request…", expanded=True) as status:
                try:
                    status.update(label="Reading Monday.com boards…", state="running")
                    client = MondayClient(monday_token)
                    deals = client.get_board(int(deals_board))
                    work_orders = client.get_board(int(work_orders_board))

                    status.update(label="Planning query with NVIDIA AI…", state="running")
                    plan = plan_query(query, deals, work_orders, nvidia_key, model)

                    if plan.get("needs_clarification") and plan.get("clarification"):
                        msg = plan["clarification"]
                        status.update(label="Clarification needed", state="complete")
                        st.markdown(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg, "plan": plan})
                    else:
                        status.update(label="Generating insights with NVIDIA NIM…", state="running")
                        msg = answer_query(query, plan, deals, work_orders, nvidia_key, model)
                        status.update(label="Analysis complete!", state="complete")
                        st.markdown(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg, "plan": plan})
                        with st.expander("Query plan / data quality"):
                            st.json(plan)

                except MondayAPIError as e:
                    status.update(label="Monday.com API error", state="error")
                    msg = f"**Monday.com error:** {e}"
                    st.error(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                except Exception as e:
                    status.update(label="Error processing query", state="error")
                    msg = f"**Unexpected error:** {e}"
                    st.error(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})

st.divider()
st.subheader("Leadership update")
if st.button("Generate leadership update"):
    if not monday_token or not deals_board or not work_orders_board:
        st.warning("Enter the Monday connection details first.")
    else:
        try:
            client = MondayClient(monday_token)
            with st.spinner("Preparing leadership update with NVIDIA AI…"):
                deals = client.get_board(int(deals_board))
                work_orders = client.get_board(int(work_orders_board))
                update = build_leadership_update(deals, work_orders, nvidia_key, model)
            st.markdown(update)
        except Exception as e:
            st.error(str(e))
