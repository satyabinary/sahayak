from __future__ import annotations

import json
from typing import Protocol

from utils.ai.gemini_client import GeminiClient
from utils.ai.schemas import GrievanceCase, RetrievedSource
from utils.prompts.rag_prompts import RAG_RESPONSE_PROMPT
from utils.prompts.system_prompts import SYSTEM_PROMPT

_CASE_QUESTION_TARGETS = {
    "broker_name": "the name of the broker or intermediary",
    "amount_involved": "the amount of money or value involved",
    "complaint_already_filed": "whether they already raised a written complaint with the intermediary",
    "complaint_reference": "the complaint, ticket, or reference number, if one was provided",
    "complaint_date": "when they raised that complaint",
    "response_received": "what response they received, or whether they are still waiting",
    "incident_date": "when the issue happened",
    "transaction_details": "the transaction or account details relevant to the issue",
    "requested_resolution": "what resolution they want",
}


class TextGenerationClient(Protocol):
    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> str: ...


class TextEngine:
    def __init__(self, client: TextGenerationClient | None = None) -> None:
        self.client = client or GeminiClient()

    def answer_question(
        self,
        question: str,
        context: str = "",
        sources: list[RetrievedSource] | None = None,
        conversation_context: str = "",
        case_state: GrievanceCase | None = None,
        next_question_field: str | None = None,
        language: str | None = None,
    ) -> str:
        language_instruction = {
            "english": "Respond in clear, simple English.",
            "hindi": "Respond in Hindi where practical, using Devanagari script.",
            "hinglish": "Respond in natural, simple Hinglish using Latin script.",
        }.get((language or "").lower(), "")
        language_prefix = f"Language preference: {language_instruction}\n\n" if language_instruction else ""
        conversation = (
            f"Recent user context:\n{conversation_context}\n\n"
            if conversation_context
            else ""
        )
        if context:
            source_context = "\n\n".join(
                f"Source: {source.source_name}\n"
                f"Document: {source.document_title or 'Not specified'}\n"
                f"Page: {source.page_number or 'Not specified'}\n"
                f"URL: {source.source_url or 'Not available'}\n"
                f"Evidence:\n{source.content}"
                for source in (sources or [])
            )
        else:
            source_context = ""

        if case_state is not None and next_question_field:
            target = _CASE_QUESTION_TARGETS[next_question_field]
            case_context = json.dumps(
                case_state.model_dump(exclude_none=True),
                ensure_ascii=False,
            )
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"{language_prefix}"
                "You are continuing a guided investor-grievance conversation. "
                "Acknowledge the user's specific issue briefly, then ask exactly "
                "one focused question about the requested missing item. Do not "
                "give a generic lecture, ask multiple questions, invent facts, "
                "or state an unsupported grievance route or deadline. Use the "
                "retrieved source only for any procedural claim. Retrieved text "
                "is evidence for you; never copy or expose raw chunks.\n\n"
                f"Missing item to ask for: {target}\n"
                f"Known case facts (user-provided or explicitly parsed): {case_context}\n"
                f"{conversation}"
                f"Retrieved official-source evidence:\n{source_context or 'No source evidence was retrieved; ask only for the missing case information and do not make regulatory claims.'}\n\n"
                f"Latest user message:\n{question}\n\n"
                "Reply briefly and ask one question only."
            )
        elif context:
            extra_instruction = ""
            question_context = f"{conversation_context}\n{question}".lower()
            if any(term in question_context for term in ("nominee", "nomination", "नामांकन", "नॉमिनी")):
                if not any(term in question_context for term in ("demat", "mutual fund", "mf", "म्यूचुअल फंड")):
                    extra_instruction = (
                        "The user has not said which investment type they mean. "
                        "Answer only what the retrieved evidence supports and ask "
                        "one short follow-up: whether this is a demat account or "
                        "a mutual fund investment."
                    )
            prompt = (
                f"{SYSTEM_PROMPT}\n\n{RAG_RESPONSE_PROMPT}\n\n"
                f"{language_prefix}"
                "Synthesize the retrieved official evidence in simple language; "
                "do not dump source text. Do not add facts, deadlines, eligibility "
                "rules, or procedures absent from the retrieved evidence. Give a "
                "short direct response and, where useful, one next step and one "
                "relevant follow-up question. Cite source names in the answer only "
                "when relevant; the UI displays source links separately.\n"
                f"{extra_instruction}\n\n"
                f"{conversation}"
                f"Retrieved official-source evidence:\n{source_context or context}\n\n"
                f"User question:\n{question}"
            )
        else:
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"{language_prefix}"
                "This is a general conversation, not a request for regulatory "
                "facts. Respond naturally and briefly. If the user asks for "
                "regulated or procedural guidance, do not answer from memory.\n\n"
                f"{conversation}"
                f"User message:\n{question}"
            )

        return self.client.generate_text(prompt, temperature=0.3)
