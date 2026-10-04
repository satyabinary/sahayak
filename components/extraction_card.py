import streamlit as st


def render_extraction_card(case_data: dict) -> None:
    st.subheader("Detected information")
    cols = st.columns(4)
    labels = ["Broker Name", "DP ID", "Client ID", "Depository"]
    values = [
        case_data.get("broker_name", ""),
        case_data.get("dp_id", ""),
        case_data.get("client_id", ""),
        case_data.get("depository", ""),
    ]
    for idx, (label, value) in enumerate(zip(labels, values)):
        with cols[idx]:
            st.metric(label, value or "—")
