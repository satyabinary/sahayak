import streamlit as st


def render_header() -> None:
    st.markdown(
        """
        <div style='padding:12px 0 8px 0; border-bottom: 1px solid #dfe3e8;'>
            <h1 style='margin:0; font-size:2.1rem;'>Sangyan Sahayak</h1>
            <p style='margin:6px 0 0 0; color:#4b5563;'>AI Investor Protection Assistant</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
