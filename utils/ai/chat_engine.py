from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from utils.ai.gemini_client import GeminiClient
from utils.ai.schemas import GrievanceCase, RetrievedSource
from utils.ai.text_engine import TextEngine
from utils.rag.retriever import Retriever

logger = logging.getLogger(__name__)

UNVERIFIED_RESPONSE = (
    "I could not verify this from the available official sources. "
    "Please check the relevant official SEBI/intermediary instructions."
)

_REGULATORY_TERMS = re.compile(
    r"\b("
    r"broker|broking|intermediar(?:y|ies)|sebi|scores|complaint|grievance|funds?|"
    r"investor|shares?|demat|depository|dp id|client id|nominee|nomination|"
    r"refund|unclaimed|iepf|claim|dividend|securities|trade|transaction|"
    r"account|ipo|rights issue|corporate action|"
    r"शिकायत|शेयर|ब्रोकर|सेबी|नामांकित|नॉमिनी|डिमैट|रिफंड|"
    r"mera broker|meri complaint|mera fund|mere paise|kya kar(?:u|na)|kaise kar(?:u|e|en)|"
    r"mujhe kya karna|response nahi|reply nahi"
    r")\b",
    re.IGNORECASE,
)

_GRIEVANCE_TERMS = re.compile(
    r"\b("
    r"complaint|grievance|refund|funds? return|money return|broker.*(?:return|response|reply|complaint)|"
    r"(?:return|refund).*(?:fund|money|amount|paise)|"
    r"not received|not returned|response nahi|reply nahi|jawab nahi|"
    r"paisa.*(?:nahi|return)|paise.*(?:nahi|return)|"
    r"mera issue|meri problem"
    r")\b",
    re.IGNORECASE,
)

_AMOUNT = re.compile(
    r"(?:₹|rs\.?\s*)\s*\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s*(?:rupees?|inr)\b",
    re.IGNORECASE,
)

_CASE_QUESTION_FIELDS = (
    "broker_name",
    "amount_involved",
    "complaint_already_filed",
    "complaint_reference",
    "complaint_date",
    "response_received",
    "incident_date",
    "transaction_details",
    "requested_resolution",
)


@dataclass
class ChatResult:
    answer: str
    mode: str
    retrieved_count: int = 0
    gemini_called: bool = False
    sources: list[RetrievedSource] = field(default_factory=list)
    retrieval_debug: list[dict[str, Any]] = field(default_factory=list)
    grievance_case: GrievanceCase | None = None
    pending_case_field: str | None = None


class RetrieverProtocol(Protocol):
    def retrieve_relevant_documents(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]: ...


class TextEngineProtocol(Protocol):
    def answer_question(
        self,
        question: str,
        context: str = "",
        sources: list[RetrievedSource] | None = None,
        conversation_context: str = "",
        case_state: GrievanceCase | None = None,
        next_question_field: str | None = None,
        language: str | None = None,
    ) -> str: ...


def is_regulatory_or_procedural_query(query: str) -> bool:
    """Route domain-specific investor-protection queries through authoritative RAG."""
    return bool(_REGULATORY_TERMS.search(query))


def _is_grievance_case(query: str, existing_case: GrievanceCase | None) -> bool:
    if existing_case and (existing_case.issue_category or existing_case.description):
        return True
    text = query.lower()
    return bool(_GRIEVANCE_TERMS.search(text)) or (
        "broker" in text
        and any(term in text for term in ("fund", "money", "paisa", "return", "response", "reply"))
    )


def _next_case_field(case: GrievanceCase) -> str | None:
    for field_name in _CASE_QUESTION_FIELDS:
        value = getattr(case, field_name)
        if field_name == "complaint_reference" and case.complaint_already_filed is not True:
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            return field_name
    return None


def _update_case_from_message(
    query: str,
    case: GrievanceCase,
    pending_field: str | None,
) -> GrievanceCase:
    updates: dict[str, Any] = {}
    text = query.strip()
    lowered = text.lower()

    if case.description is None:
        updates["description"] = text
    if case.issue_category is None:
        if any(term in lowered for term in ("fund", "refund", "money", "paisa", "paise")):
            updates["issue_category"] = "Funds not returned"
        else:
            updates["issue_category"] = "Investor grievance"
    if "broker" in lowered:
        updates["intermediary_type"] = "broker"

    negative_complaint = bool(
        re.search(
            r"(?:nahi|nahin|not|haven't|have not|didn't|did not).{0,30}(?:complaint|ticket|grievance|raise|file)",
            lowered,
        )
        or re.search(
            r"(?:complaint|ticket|grievance).{0,30}(?:nahi|nahin|not|never)",
            lowered,
        )
    )
    affirmative_complaint = bool(
        re.search(
            r"(?:haan|han|yes|already|ki thi|kiya|filed|raised|raise ki|submit ki)",
            lowered,
        )
        and any(term in lowered for term in ("complaint", "ticket", "grievance", "filed", "raised"))
    )

    if pending_field == "broker_name" and text:
        updates["broker_name"] = text
    elif pending_field == "amount_involved" and text:
        updates["amount_involved"] = text
    elif pending_field == "complaint_already_filed":
        if negative_complaint:
            updates["complaint_already_filed"] = False
        elif affirmative_complaint or re.fullmatch(r"(?:haan|han|yes|yep|correct|bilkul)[.! ]*", lowered):
            updates["complaint_already_filed"] = True
    elif pending_field in {
        "complaint_reference",
        "complaint_date",
        "response_received",
        "incident_date",
        "transaction_details",
        "requested_resolution",
    } and text:
        updates[pending_field] = text

    if case.broker_name is None:
        named_broker = re.search(
            r"(?:broker|intermediary)\s+(?:name\s+)?(?:is|called|named|ka naam)\s+([^,.;\n]+)",
            text,
            re.IGNORECASE,
        )
        if named_broker:
            updates["broker_name"] = named_broker.group(1).strip()

    if case.amount_involved is None and pending_field != "amount_involved":
        amount_match = _AMOUNT.search(text)
        if amount_match:
            updates["amount_involved"] = amount_match.group(0).strip()

    if negative_complaint:
        updates["complaint_already_filed"] = False
    elif affirmative_complaint:
        updates["complaint_already_filed"] = True

    if case.response_received is None and re.search(
        r"(?:response|reply|jawab).{0,24}(?:nahi|nahin|not|no)|"
        r"(?:nahi|nahin|no).{0,24}(?:response|reply|jawab)",
        lowered,
    ):
        updates["response_received"] = text

    return case.model_copy(update=updates)


class ChatEngine:
    def __init__(
        self,
        retriever: RetrieverProtocol | None = None,
        client: GeminiClient | None = None,
        text_engine: TextEngineProtocol | None = None,
    ) -> None:
        self.retriever = retriever or Retriever()
        self.client = client or GeminiClient()
        self.text_engine = text_engine or TextEngine(self.client)

    def handle_message(
        self,
        query: str,
        history: list[dict[str, str]] | None = None,
        grievance_case: GrievanceCase | dict[str, Any] | None = None,
        pending_case_field: str | None = None,
        language: str | None = None,
    ) -> ChatResult:
        request_id = uuid.uuid4().hex[:12]
        query_digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
        recent_history = (history or [])[-6:]
        prior_user_context = "\n".join(
            message.get("content", "")
            for message in recent_history
            if message.get("role") == "user"
        )
        routing_text = f"{prior_user_context}\n{query}".strip()
        case = (
            grievance_case
            if isinstance(grievance_case, GrievanceCase)
            else GrievanceCase.model_validate(grievance_case or {})
        )
        case_active = _is_grievance_case(routing_text, case)
        if case_active:
            case = _update_case_from_message(query, case, pending_case_field)
            next_field = _next_case_field(case)
            logger.debug(
                "chat_case_state_updated request_id=%s issue_category=%s "
                "known_fields=%s next_question_field=%s",
                request_id,
                case.issue_category,
                [
                    name
                    for name, value in case.model_dump().items()
                    if value not in (None, "", [])
                ],
                next_field,
            )
        else:
            next_field = None
        logger.debug(
            "chat_request_started request_id=%s query_digest=%s query_characters=%d",
            request_id,
            query_digest,
            len(query),
        )

        if not case_active and not is_regulatory_or_procedural_query(routing_text):
            logger.debug("chat_rag_skipped request_id=%s reason=general_conversation", request_id)
            logger.debug("chat_gemini_call_started request_id=%s mode=general", request_id)
            language_kwargs = {"language": language} if language else {}
            answer = self.text_engine.answer_question(
                query,
                conversation_context=prior_user_context,
                **language_kwargs,
            )
            logger.debug("chat_gemini_call_succeeded request_id=%s mode=general", request_id)
            return ChatResult(answer=answer, mode="general", gemini_called=True)

        logger.debug("chat_rag_invoked request_id=%s", request_id)
        case_query_context = ""
        if case_active and case is not None:
            case_query_context = " ".join(
                value
                for value in (
                    case.issue_category,
                    case.description,
                    case.transaction_details,
                    case.broker_name,
                )
                if value
            )
        retrieval_query = f"{case_query_context}\n{prior_user_context}\n{query}".strip()
        retrieved = self.retriever.retrieve_relevant_documents(retrieval_query, top_k=5)
        logger.debug(
            "chat_rag_completed request_id=%s retrieved_count=%d",
            request_id,
            len(retrieved),
        )
        sources: list[RetrievedSource] = []
        retrieval_debug: list[dict[str, Any]] = []
        for item in retrieved:
            metadata = item.get("metadata") or {}
            distance = item.get("distance")
            retrieval_debug.append(
                {
                    "source_id": metadata.get("source_id"),
                    "source_name": metadata.get("source_name"),
                    "document_title": metadata.get("document_title"),
                    "page_number": metadata.get("page_number"),
                    "distance": distance,
                    "relevance": item.get("relevance"),
                }
            )
            logger.debug(
                "chat_rag_result request_id=%s source_id=%s source_name=%s "
                "document_title=%s page=%s distance=%s relevance=%s",
                request_id,
                metadata.get("source_id"),
                metadata.get("source_name"),
                metadata.get("document_title"),
                metadata.get("page_number"),
                distance,
                item.get("relevance"),
            )
            sources.append(
                RetrievedSource(
                    source_name=metadata.get("source_name") or "Official source",
                    source_url=metadata.get("source_url"),
                    document_title=metadata.get("document_title"),
                    page_number=metadata.get("page_number"),
                    section=metadata.get("section"),
                    content=item.get("content", ""),
                    score=item.get("relevance"),
                )
            )

        if not sources:
            if case_active and next_field:
                logger.debug(
                    "chat_case_intake_without_sources request_id=%s next_question_field=%s",
                    request_id,
                    next_field,
                )
                language_kwargs = {"language": language} if language else {}
                answer = self.text_engine.answer_question(
                    query,
                    conversation_context=prior_user_context,
                    case_state=case,
                    next_question_field=next_field,
                    **language_kwargs,
                )
                return ChatResult(
                    answer=answer,
                    mode="case_intake",
                    gemini_called=True,
                    grievance_case=case,
                    pending_case_field=next_field,
                )
            logger.debug("chat_gemini_call_skipped request_id=%s reason=no_official_context", request_id)
            return ChatResult(
                answer=UNVERIFIED_RESPONSE,
                mode="regulatory",
                retrieved_count=0,
                gemini_called=False,
                grievance_case=case if case_active else None,
            )

        logger.debug("chat_gemini_call_started request_id=%s mode=grounded_rag", request_id)
        context = "\n\n".join(source.content for source in sources)
        language_kwargs = {"language": language} if language else {}
        answer = self.text_engine.answer_question(
            query,
            context=context,
            sources=sources,
            conversation_context=prior_user_context,
            case_state=case if case_active else None,
            next_question_field=next_field,
            **language_kwargs,
        )
        logger.debug("chat_gemini_call_succeeded request_id=%s mode=grounded_rag", request_id)
        return ChatResult(
            answer=answer,
            mode="case_intake" if case_active and next_field else "regulatory",
            retrieved_count=len(sources),
            gemini_called=True,
            sources=sources,
            retrieval_debug=retrieval_debug,
            grievance_case=case if case_active else None,
            pending_case_field=next_field,
        )
