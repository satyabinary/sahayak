import streamlit as st


def render_sources(sources: list[dict]) -> None:
    if not sources:
        st.caption("No official-source citations available for this response.")
        return

    st.markdown("### Sources")
    seen: set[tuple[str, str, str]] = set()
    for item in sources:
        source_name = item.get("source_name", "Official source")
        source_url = item.get("source_url") or ""
        page_number = item.get("page_number")
        citation_key = (
            source_url,
            item.get("document_title") or source_name,
            str(page_number or ""),
        )
        if citation_key in seen:
            continue
        seen.add(citation_key)

        page = f"Page {page_number}" if page_number else "Page not specified"
        document = item.get("document_title")
        st.markdown(f"- **{source_name}** — {document or 'Document not specified'} — {page}")
        if source_url:
            st.markdown(f"  [{source_url}]({source_url})")
