"""Chatbot-style Streamlit demo for the Query Recommender API.

Run with:
    streamlit run app.py
"""

import os

import requests
import streamlit as st

API_ENDPOINTS = {
    "Local": os.getenv("QR_API_URL", "http://localhost:5000/api/v1"),
    "Remote (dev)": "https://datagems-dev.scayle.es/qr/api/v1",
}

st.set_page_config(page_title="Query Recommender", page_icon="💬")

if "messages" not in st.session_state:
    # Each message: {"role": "user" | "assistant", "content": str, "suggestions": list[str]}
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

with st.sidebar:
    st.header("Settings")
    api_choice = st.radio("API", [*API_ENDPOINTS, "Custom"], horizontal=True)
    if api_choice == "Custom":
        api_url = st.text_input("API base URL", value=API_ENDPOINTS["Local"])
    else:
        api_url = API_ENDPOINTS[api_choice]
        st.caption(f"`{api_url}`")
    api_url = api_url.rstrip("/")
    user_id = st.text_input(
        "User ID (optional)",
        value="user1",
        help="Sent in the request context so recommendations can use the user's profile.",
    )
    timeout = st.number_input("Timeout (s)", min_value=5, max_value=300, value=60)

    if st.button("Check API status"):
        try:
            r = requests.get(api_url, timeout=5)
            r.raise_for_status()
            st.success(r.json().get("message", "API is up"))
        except Exception as e:
            st.error(f"API unreachable: {e}")

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()


def recommend(query: str) -> list[str]:
    context = {"user_id": user_id} if user_id else None
    r = requests.post(
        f"{api_url}/recommend-next-queries",
        json={"current_query": query, "context": context},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["next_queries"]


def pick_suggestion(query: str):
    st.session_state.pending_query = query


st.title("💬 Query Recommender")
st.caption("Ask something in natural language and get suggestions for what to ask next.")

last_idx = len(st.session_state.messages) - 1
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for j, s in enumerate(msg.get("suggestions") or []):
            # Only the latest set of suggestions is clickable
            st.button(
                s,
                key=f"sugg_{i}_{j}",
                on_click=pick_suggestion,
                args=(s,),
                disabled=i != last_idx,
                use_container_width=True,
            )

# New query comes either from the chat box or from a clicked suggestion
typed = st.chat_input("Ask a question…")
query = typed or st.session_state.pending_query
st.session_state.pending_query = None

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking of what you might ask next…"):
            try:
                suggestions = recommend(query)
                content = "Here are some queries you might want to ask next:"
            except Exception as e:
                suggestions = []
                content = f"⚠️ Could not get recommendations: `{e}`"

    st.session_state.messages.append(
        {"role": "assistant", "content": content, "suggestions": suggestions}
    )
    st.rerun()
