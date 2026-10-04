import streamlit as st


def show_status_badge(text: str, kind: str = "info") -> None:
    palette = {"info": "#e0f2fe", "success": "#dcfce7", "warning": "#fef3c7", "error": "#fee2e2"}
    color = palette.get(kind, "#e0f2fe")
    st.markdown(
        f"<div style='background-color:{color}; padding:10px 12px; border-radius:8px; border:1px solid #d1d5db; margin:8px 0;'>{text}</div>",
        unsafe_allow_html=True,
    )
