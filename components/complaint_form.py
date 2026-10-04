import streamlit as st


def render_case_form(case: dict[str, str]) -> dict[str, str]:
    st.subheader("Grievance details")
    with st.form("case_form"):
        case["investor_name"] = st.text_input("Investor name", value=case.get("investor_name", ""))
        case["broker_name"] = st.text_input("Broker / intermediary involved", value=case.get("broker_name", ""))
        case["issue_category"] = st.text_input("Issue category", value=case.get("issue_category", ""))
        case["amount_involved"] = st.text_input("Amount involved", value=case.get("amount_involved", ""))
        case["incident_date"] = st.text_input("Date of incident", value=case.get("incident_date", ""))
        case["description"] = st.text_area("What happened?", value=case.get("description", ""), height=140)
        case["steps_already_taken"] = st.text_area("Steps already taken", value=case.get("steps_already_taken", ""), height=120)
        case["requested_resolution"] = st.text_area("Requested resolution", value=case.get("requested_resolution", ""), height=120)
        submitted = st.form_submit_button("Save case")
        if submitted:
            st.success("Case details saved.")
    return case
