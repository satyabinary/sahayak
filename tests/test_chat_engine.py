from utils.ai.chat_engine import (
    UNVERIFIED_RESPONSE,
    ChatEngine,
    is_regulatory_or_procedural_query,
)
from utils.ai.gemini_client import GeminiClient
from utils.rag.retriever import Retriever
from utils.ai.schemas import GrievanceCase, RetrievedSource
from utils.ai.text_engine import TextEngine


class FakeRetriever(Retriever):
    def __init__(self, results=None):
        self.results = results or []
        self.calls = []

    def retrieve_relevant_documents(self, query, top_k=None):
        self.calls.append((query, top_k))
        return self.results


class FakeTextEngine(TextEngine):
    def __init__(self):
        self.calls = []

    def answer_question(
        self,
        question,
        context="",
        sources=None,
        conversation_context="",
        case_state=None,
        next_question_field=None,
    ):
        self.calls.append(
            {
                "question": question,
                "context": context,
                "sources": sources,
                "conversation_context": conversation_context,
                "case_state": case_state,
                "next_question_field": next_question_field,
            }
        )
        return f"Gemini-style response for: {question}"


def test_exact_chat_examples_route_correctly():
    queries = [
        ("hi", False),
        ("mera broker response nahi de raha", True),
        ("nominee ki details kese dekhu", True),
        ("mujhe SEBI SCORES ke through complaint kaise karni hai", True),
    ]
    for query, expected in queries:
        assert is_regulatory_or_procedural_query(query) is expected


def test_nomination_question_uses_rag():
    evidence = {
        "content": "SEBI investor nomination guidance fixture.",
        "metadata": {
            "source_id": "nomination",
            "source_name": "SEBI Investor",
            "source_url": "https://investor.sebi.gov.in/market-nomination.html",
            "document_title": "Nomination",
        },
        "distance": 0.2,
        "relevance": 0.8,
    }
    retriever = FakeRetriever([evidence])
    text_engine = FakeTextEngine()
    engine = ChatEngine(retriever=retriever, text_engine=text_engine)

    result = engine.handle_message("nominee kaise add kar sakta hu?")

    assert result.mode == "regulatory"
    assert result.retrieved_count == 1
    assert result.sources[0].source_name == "SEBI Investor"
    assert "nomination" in text_engine.calls[0]["context"].lower()


def test_nomination_answer_prompt_asks_account_type_without_dumping_chunks():
    class PromptCaptureClient(GeminiClient):
        prompt = ""

        def generate_text(
            self,
            prompt,
            *,
            temperature=0.2,
            max_output_tokens=None,
        ):
            self.prompt = prompt
            self.temperature = temperature
            self.max_output_tokens = max_output_tokens
            return "A complete answer."

    client = PromptCaptureClient()
    engine = TextEngine(client=client)
    source = RetrievedSource(
        source_name="SEBI Investor",
        source_url="https://investor.sebi.gov.in/market-nomination.html",
        document_title="Nomination",
        content="Official evidence fixture about nomination.",
    )

    answer = engine.answer_question(
        "nominee kaise add kar sakta hu?",
        context=source.content,
        sources=[source],
    )

    assert answer == "A complete answer."
    assert "demat account or a mutual fund investment" in client.prompt
    assert "Official evidence fixture" in client.prompt


def test_casual_message_calls_gemini_without_rag():
    retriever = FakeRetriever()
    text_engine = FakeTextEngine()
    engine = ChatEngine(retriever=retriever, text_engine=text_engine)

    result = engine.handle_message("hi")

    assert result.mode == "general"
    assert result.gemini_called is True
    assert result.retrieved_count == 0
    assert retriever.calls == []
    assert text_engine.calls[0]["context"] == ""


def test_regulatory_query_uses_retrieval_then_grounded_gemini():
    retrieved = {
        "content": "Official test fixture content about grievance filing.",
        "metadata": {
            "source_id": "fixture",
            "source_name": "Official test source",
            "source_url": "https://example.gov/",
            "document_title": "Fixture guidance",
            "page_number": 2,
            "section": None,
        },
        "distance": 0.2,
        "relevance": 1 / 1.2,
    }
    retriever = FakeRetriever([retrieved])
    text_engine = FakeTextEngine()
    engine = ChatEngine(retriever=retriever, text_engine=text_engine)

    result = engine.handle_message("mera broker response nahi de raha")

    assert len(retriever.calls) == 1
    assert "mera broker response nahi de raha" in retriever.calls[0][0]
    assert retriever.calls[0][1] == 5
    assert result.mode == "case_intake"
    assert result.gemini_called is True
    assert result.retrieved_count == 1
    assert result.sources[0].source_name == "Official test source"
    assert "Official test fixture content" in text_engine.calls[0]["context"]
    assert result.pending_case_field == "broker_name"


def test_follow_up_retains_recent_investor_context():
    retriever = FakeRetriever()
    text_engine = FakeTextEngine()
    engine = ChatEngine(retriever=retriever, text_engine=text_engine)

    result = engine.handle_message(
        "what should I do next?",
        history=[{"role": "user", "content": "My broker has not responded to my complaint"}],
        grievance_case={
            "issue_category": "Funds not returned",
            "description": "My broker has not responded to my complaint",
            "broker_name": "Example broker",
        },
    )

    assert result.mode == "case_intake"
    assert retriever.calls[0][1] == 5
    assert "My broker has not responded" in retriever.calls[0][0]


def test_regulatory_query_without_sources_stops_with_safe_fallback():
    retriever = FakeRetriever()
    text_engine = FakeTextEngine()
    engine = ChatEngine(retriever=retriever, text_engine=text_engine)

    result = engine.handle_message("nominee ki details kese dekhu")

    assert result.answer == UNVERIFIED_RESPONSE
    assert result.mode == "regulatory"
    assert result.gemini_called is False
    assert result.retrieved_count == 0
    assert text_engine.calls == []


def test_case_conversation_asks_one_next_item_in_order():
    text_engine = FakeTextEngine()
    retriever = FakeRetriever()
    engine = ChatEngine(retriever=retriever, text_engine=text_engine)
    case = GrievanceCase().model_dump()

    first = engine.handle_message(
        "mere broker ne mera fund return nahi kiya aur 4-5 din se response bhi nahi diya",
        grievance_case=case,
    )
    assert first.pending_case_field == "broker_name"
    assert first.grievance_case is not None
    assert first.grievance_case.description == (
        "mere broker ne mera fund return nahi kiya aur 4-5 din se response bhi nahi diya"
    )
    assert first.grievance_case.response_received is not None

    case = first.grievance_case.model_dump()
    second = engine.handle_message(
        "Zerodha",
        grievance_case=case,
        pending_case_field=first.pending_case_field,
    )
    assert second.grievance_case is not None
    assert second.grievance_case.broker_name == "Zerodha"
    assert second.pending_case_field == "amount_involved"

    case = second.grievance_case.model_dump()
    third = engine.handle_message(
        "₹12,000",
        grievance_case=case,
        pending_case_field=second.pending_case_field,
    )
    assert third.grievance_case is not None
    assert third.grievance_case.amount_involved == "₹12,000"
    assert third.pending_case_field == "complaint_already_filed"

    case = third.grievance_case.model_dump()
    fourth = engine.handle_message(
        "haan maine broker ko complaint bhi ki thi",
        grievance_case=case,
        pending_case_field=third.pending_case_field,
    )
    assert fourth.grievance_case is not None
    assert fourth.grievance_case.complaint_already_filed is True
    assert fourth.pending_case_field == "complaint_reference"


def test_long_regulatory_message_is_not_sliced():
    long_message = (
        "Please explain the official grievance guidance and next steps. "
        * 100
    )
    assert len(long_message) > 1200
    assert long_message[-1] == " "
    retrieved = {
        "content": "Official grievance guidance fixture.",
        "metadata": {
            "source_id": "fixture",
            "source_name": "Official test source",
            "source_url": "https://example.gov/",
        },
        "distance": 0.2,
    }
    text_engine = FakeTextEngine()
    engine = ChatEngine(
        retriever=FakeRetriever([retrieved]),
        text_engine=text_engine,
    )

    engine.handle_message(long_message)

    assert text_engine.calls[0]["question"] == long_message
