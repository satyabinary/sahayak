import streamlit as st


def render_chat_history() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])


def add_user_message(text: str) -> None:
    st.session_state.chat_history.append({"role": "user", "content": text})


def add_assistant_message(text: str) -> None:
    st.session_state.chat_history.append({"role": "assistant", "content": text})
