import streamlit as st


def render_sidebar() -> str:
    st.sidebar.title("Navigation")
    pages = [
        "Home",
        "Ask Sangyan",
        "File a Grievance",
        "Extract DP Details",
        "Complaint Draft",
        "IEPF Guidance",
        "About / Sources",
    ]
    return st.sidebar.radio("Go to", pages, index=0)
