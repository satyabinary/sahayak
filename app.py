from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from components.chat_ui import add_assistant_message, add_user_message, render_chat_history
from components.complaint_form import render_case_form
from components.extraction_card import render_extraction_card
from components.header import render_header
from components.sidebar import render_sidebar
from components.source_citations import render_sources
from utils.ai.chat_engine import ChatEngine
from utils.ai.gemini_client import GeminiClient, GeminiClientError, GeminiRateLimitError
from utils.ai.schemas import GrievanceCase
from utils.ai.vision_engine import VisionEngine
from utils.config import Settings, ensure_directories
from utils.rag.ingestion import KnowledgeBaseIngestor
from utils.rag.retriever import Retriever
from utils.security.redaction import safe_log_data
from utils.validation.investor_data import required_missing
from utils.pdf.pdf_generator import generate_pdf

LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=LOG_LEVEL)
logging.getLogger().setLevel(LOG_LEVEL)
logger = logging.getLogger("sangyan")


@st.cache_resource
def get_gemini_client() -> GeminiClient:
    return GeminiClient()


@st.cache_resource
def get_ingestor() -> KnowledgeBaseIngestor:
    return KnowledgeBaseIngestor()


@st.cache_resource
def get_retriever() -> Retriever:
    return Retriever()


@st.cache_resource
def get_chat_engine() -> ChatEngine:
    return ChatEngine(retriever=get_retriever(), client=get_gemini_client())


def init_app() -> None:
    ensure_directories()
    try:
        settings = Settings.from_env()
        st.session_state.settings = settings
    except ValueError:
        st.error("GEMINI_API_KEY not configured. Create a .env file with your Gemini key and restart the app.")
        st.info("Example: copy .env.example to .env and set GEMINI_API_KEY=your_real_key")
        st.stop()


def render_home() -> None:
    st.title("How can we help you today?")
    st.markdown("""
    <style>
    .stButton > button { height: 3.2em; width: 100%; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)
    cards = [
        ("Ask Sangyan", "Get simple, step-by-step guidance on investor grievances."),
        ("File a Grievance", "Build your case and prepare the complaint flow."),
        ("Extract DP Details", "Upload a screenshot and extract broker / DP details."),
        ("Complaint Draft", "Review and generate a complaint draft."),
        ("IEPF Guidance", "Understand official-source guidance for possible IEPF-related matters."),
    ]
    for title, description in cards:
        with st.container():
            st.markdown(f"<div style='margin:10px 0; padding:16px; border:1px solid #dfe3e8; border-radius:12px; background:#f8fafc;'><strong>{title}</strong><br>{description}</div>", unsafe_allow_html=True)


def render_ask_sangyan() -> None:
    st.subheader("Ask Sangyan")
    render_chat_history()
    if prompt := st.chat_input("Aap apni sawal likhein..."):
        add_user_message(prompt)
        if "grievance_case" not in st.session_state:
            st.session_state.grievance_case = GrievanceCase().model_dump()
        if "pending_case_field" not in st.session_state:
            st.session_state.pending_case_field = None
        with st.spinner("Sangyan is preparing a response..."):
            try:
                previous_history = st.session_state.chat_history[:-1]
                result = get_chat_engine().handle_message(
                    prompt,
                    history=previous_history,
                    grievance_case=st.session_state.grievance_case,
                    pending_case_field=st.session_state.pending_case_field,
                )
                add_assistant_message(result.answer)
                if result.grievance_case is not None:
                    st.session_state.grievance_case = result.grievance_case.model_dump()
                    st.session_state.pending_case_field = result.pending_case_field
                st.session_state.last_chat_sources = [
                    source.model_dump() for source in result.sources
                ]
                st.rerun()
            except GeminiRateLimitError as exc:
                add_assistant_message(str(exc))
                st.rerun()
            except GeminiClientError:
                add_assistant_message(
                    "The AI service is temporarily unavailable. Please try again shortly."
                )
                st.rerun()
            except Exception as exc:
                logger.error("Chat processing failed error_type=%s", type(exc).__name__)
                add_assistant_message("The AI service could not answer the question right now. Please try again in a moment.")
                st.rerun()
    if st.session_state.get("last_chat_sources"):
        render_sources(st.session_state.last_chat_sources)


def render_case_builder() -> None:
    st.subheader("File a Grievance")
    if "case_data" not in st.session_state:
        st.session_state.case_data = {
            "investor_name": "",
            "contact": "",
            "broker_name": "",
            "dp_id": "",
            "client_id": "",
            "security_name": "",
            "issue_category": "",
            "incident_date": "",
            "amount_involved": "",
            "description": "",
            "steps_already_taken": "",
            "requested_resolution": "",
            "supporting_documents": [],
        }
    case = st.session_state.case_data
    render_case_form(case)
    st.session_state.case_data = case
    missing = required_missing(case)
    if missing:
        st.warning("Missing required details: " + ", ".join(missing))


def render_extraction_ui() -> None:
    st.subheader("Extract DP Details")
    uploaded_file = st.file_uploader("Upload a broker or depository screenshot", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        if uploaded_file.size > int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024:
            st.error("The image is larger than the allowed size. Please upload a smaller screenshot.")
            return
        temp_path = Path("./data/uploads") / f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
        temp_path.write_bytes(uploaded_file.getvalue())
        try:
            extraction = VisionEngine(get_gemini_client()).extract_dp_details(str(temp_path))
            st.session_state.extracted_data = extraction.model_dump()
            render_extraction_card(extraction.model_dump())
            st.write("Confidence / verification notice")
            st.caption("Please verify this value from your broker or depository statement before using it in the complaint.")
            for value in extraction.model_dump().get("confidence", {}).values():
                st.progress(float(value))
            if extraction.warnings:
                st.warning("\n".join(extraction.warnings))
        except Exception as exc:
            logger.exception("Vision extraction failed: %s", safe_log_data(str(exc)))
            st.error("The AI service could not analyze the uploaded image. Please try again in a moment.")
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass


def render_complaint_draft() -> None:
    st.subheader("Complaint Draft")
    if "case_data" not in st.session_state:
        st.session_state.case_data = {}
    case = st.session_state.case_data
    if st.button("Generate complaint draft"):
        with st.spinner("Preparing the complaint draft..."):
            try:
                retriever = get_retriever()
                matching = retriever.retrieve_relevant_documents(case.get("issue_category", "investor grievance guidance"), top_k=4)
                context = "\n\n".join(item["content"] for item in matching)
                helper_prompt = f"Generate a complaint draft using only the provided case data and the retrieved official-source context.\nCase data:\n{json.dumps(case, ensure_ascii=False)}\n\nContext:\n{context}\n\nDo not invent missing facts."
                draft_text = get_gemini_client().generate_text(helper_prompt, temperature=0.2, max_output_tokens=1200)
                st.text_area("Draft", draft_text, height=400)
                st.download_button("Download as PDF", generate_pdf(draft_text), file_name="complaint_draft.pdf", mime="application/pdf")
            except Exception as exc:
                logger.exception("Complaint generation failed: %s", safe_log_data(str(exc)))
                st.error("The complaint draft could not be generated. Please check the case details and try again.")


def render_iepf_guidance() -> None:
    st.subheader("IEPF Guidance")
    question = st.text_input("Describe your situation")
    if st.button("Get official-source guidance") and question:
        with st.spinner("Checking official-source guidance..."):
            try:
                retriever = get_retriever()
                results = retriever.retrieve_relevant_documents(question, top_k=4)
                context = "\n\n".join(item["content"] for item in results)
                response = get_gemini_client().generate_text(f"Use the following official guidance to answer the question. If insufficient, say so. Context:\n{context}\n\nUser question:\n{question}")
                st.markdown(response)
                render_sources([item["metadata"] for item in results])
            except Exception as exc:
                logger.exception("IEPF guidance failed: %s", safe_log_data(str(exc)))
                st.error("The guidance service could not retrieve the supporting material right now.")


def render_about() -> None:
    st.subheader("About / Sources")
    st.markdown("This app provides educational and procedural guidance, not legal advice. Final complaint submission should be verified through official regulator or intermediary instructions.")
    st.markdown("- SEBI SCORES: https://scores.sebi.gov.in/")
    st.markdown("- SEBI Investor Education: https://www.sebi.gov.in/")
    st.markdown("- MCA / IEPF guidance: https://www.mca.gov.in/")


def render_developer_diagnostics() -> None:
    st.sidebar.divider()
    if st.session_state.get("settings") and st.session_state.settings.app_env.lower() in {
        "development",
        "test",
    }:
        if st.sidebar.checkbox("Developer diagnostics", value=False):
            with st.expander("Developer diagnostics", expanded=True):
                try:
                    status = get_retriever().vector_store.diagnostics()
                    st.write("RAG / ChromaDB")
                    st.json(status)
                except Exception as exc:
                    st.error(f"ChromaDB diagnostic failed: {type(exc).__name__}")
                st.write("Gemini")
                st.write(
                    "Client initialized"
                    if get_gemini_client().client is not None
                    else "Client unavailable"
                )
                if st.button("Test Gemini connection"):
                    try:
                        response = get_gemini_client().generate_text(
                            "Reply with the single word OK.", max_output_tokens=8
                        )
                        st.success(f"Gemini responded ({len(response)} characters).")
                    except Exception as exc:
                        st.error(f"Gemini request failed: {type(exc).__name__}")
                if st.button("Sync official-source knowledge base"):
                    with st.spinner("Fetching configured official sources and indexing them..."):
                        try:
                            report = get_ingestor().ingest()
                            st.json(report)
                        except Exception as exc:
                            st.error(f"Knowledge-base sync failed: {type(exc).__name__}")
                if st.button("Run retrieval diagnostic"):
                    try:
                        results = get_retriever().retrieve_relevant_documents(
                            "SEBI SCORES investor complaint grievance", top_k=5
                        )
                        st.write(f"Retrieved results: {len(results)}")
                        st.json(
                            [
                                {
                                    "metadata": item.get("metadata"),
                                    "distance": item.get("distance"),
                                    "relevance": item.get("relevance"),
                                }
                                for item in results
                            ]
                        )
                    except Exception as exc:
                        st.error(f"Retrieval diagnostic failed: {type(exc).__name__}")


def main() -> None:
    init_app()
    render_header()
    page = render_sidebar()
    render_developer_diagnostics()
    if page == "Home":
        render_home()
    elif page == "Ask Sangyan":
        render_ask_sangyan()
    elif page == "File a Grievance":
        render_case_builder()
    elif page == "Extract DP Details":
        render_extraction_ui()
    elif page == "Complaint Draft":
        render_complaint_draft()
    elif page == "IEPF Guidance":
        render_iepf_guidance()
    else:
        render_about()


if __name__ == "__main__":
    main()
