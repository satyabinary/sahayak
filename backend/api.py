from __future__ import annotations

import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Literal

import yaml
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from utils.ai.chat_engine import ChatEngine, UNVERIFIED_RESPONSE
from utils.ai.gemini_client import GeminiClient, GeminiClientError, GeminiRateLimitError
from utils.ai.schemas import GrievanceCase
from utils.ai.vision_engine import VisionEngine
from utils.config import settings
from utils.pdf.pdf_generator import generate_pdf
from utils.rag.retriever import Retriever

logger = logging.getLogger(__name__)

app = FastAPI(title="Sangyan Sahayak API", version="1.0.0")
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(StarletteHTTPException)
async def safe_http_error(_: Request, error: StarletteHTTPException) -> JSONResponse:
    detail = error.detail if isinstance(error.detail, str) else "The request could not be completed."
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": "request_error", "message": detail}},
        headers=error.headers,
    )


@app.exception_handler(RequestValidationError)
async def safe_validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": "Please check the submitted information."}},
    )


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=12000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=40)
    language: Literal["hinglish", "hindi", "english"] = "hinglish"
    case: GrievanceCase = Field(default_factory=GrievanceCase)
    pending_case_field: str | None = None


class CaseRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    case: GrievanceCase


class ComplaintRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    case: GrievanceCase


class PdfRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50000)


class IepfRequest(BaseModel):
    question: str = Field(min_length=1, max_length=12000)
    language: Literal["hinglish", "hindi", "english"] = "hinglish"


_cases: dict[str, GrievanceCase] = {}
_cases_lock = threading.Lock()


def _safe_sources(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_name": item.get("source_name") or "Official source",
            "source_url": item.get("source_url"),
            "document_title": item.get("document_title"),
            "page_number": item.get("page_number"),
            "section": item.get("section"),
            "score": item.get("relevance"),
        }
        for item in items
    ]


def _sources_from_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retriever results keep source details inside item["metadata"]; flatten them first."""
    return _safe_sources(
        [
            {
                "source_name": (item.get("metadata") or {}).get("source_name"),
                "source_url": (item.get("metadata") or {}).get("source_url"),
                "document_title": (item.get("metadata") or {}).get("document_title"),
                "page_number": (item.get("metadata") or {}).get("page_number"),
                "section": (item.get("metadata") or {}).get("section"),
                "relevance": item.get("relevance"),
            }
            for item in matches
        ]
    )


def _raise_service_error(error: Exception) -> None:
    logger.error("api_service_failed error_type=%s", type(error).__name__)
    if isinstance(error, GeminiRateLimitError):
        raise HTTPException(status_code=429, detail=str(error)) from error
    if isinstance(error, GeminiClientError):
        raise HTTPException(status_code=502, detail="The AI service could not complete the request.") from error
    raise HTTPException(status_code=500, detail="The request could not be completed.") from error


def _load_source_registry() -> list[dict[str, Any]]:
    path = Path("knowledge_base/sources.yaml")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}
    return payload.get("sources", [])


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "Sangyan Sahayak API",
        "max_upload_mb": settings.max_upload_mb,
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    try:
        engine = ChatEngine()
        result = engine.handle_message(
            request.message,
            history=[item.model_dump() for item in request.history],
            grievance_case=request.case,
            pending_case_field=request.pending_case_field,
            language=request.language,
        )
        if result.grievance_case is not None:
            with _cases_lock:
                _cases[request.session_id] = result.grievance_case
        logger.info(
            "api_chat_completed mode=%s rag_results=%d gemini_called=%s",
            result.mode,
            result.retrieved_count,
            result.gemini_called,
        )
        return {
            "answer": result.answer,
            "sources": _safe_sources(
                [
                    {
                        "source_name": source.source_name,
                        "source_url": source.source_url,
                        "document_title": source.document_title,
                        "page_number": source.page_number,
                        "section": source.section,
                        "relevance": source.score,
                    }
                    for source in result.sources
                ]
            ),
            "case": result.grievance_case.model_dump() if result.grievance_case else None,
            "pending_case_field": result.pending_case_field,
        }
    except HTTPException:
        raise
    except Exception as error:
        _raise_service_error(error)


@app.get("/api/grievance/{session_id}")
def get_grievance(session_id: str) -> dict[str, Any]:
    with _cases_lock:
        case = _cases.get(session_id, GrievanceCase())
    return {"session_id": session_id, "case": case.model_dump()}


@app.post("/api/grievance")
def save_grievance(request: CaseRequest) -> dict[str, Any]:
    with _cases_lock:
        _cases[request.session_id] = request.case
    return {"session_id": request.session_id, "case": request.case.model_dump()}


@app.post("/api/vision/extract")
def extract_vision(image: UploadFile = File(...)) -> dict[str, Any]:
    maximum = settings.max_upload_mb * 1024 * 1024
    data = image.file.read(maximum + 1)
    if not data or len(data) > maximum:
        raise HTTPException(
            status_code=413 if len(data) > maximum else 400,
            detail=f"Upload must be a non-empty image no larger than {settings.max_upload_mb} MB.",
        )
    signatures = {
        b"\x89PNG\r\n\x1a\n": ".png",
        b"\xff\xd8\xff": ".jpg",
    }
    suffix = next((extension for signature, extension in signatures.items() if data.startswith(signature)), None)
    if suffix is None:
        raise HTTPException(status_code=415, detail="Only valid PNG and JPEG images are supported.")

    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(data)
            temporary_path = temp_file.name
        extraction = VisionEngine().extract_dp_details(temporary_path)
        return extraction.model_dump()
    except Exception as error:
        _raise_service_error(error)
    finally:
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)


@app.post("/api/complaint/draft")
def create_complaint_draft(request: ComplaintRequest) -> dict[str, Any]:
    try:
        retriever = Retriever()
        query = " ".join(
            value
            for value in (request.case.issue_category, request.case.description, request.case.broker_name)
            if value
        ) or "investor grievance complaint procedure"
        matches = retriever.retrieve_relevant_documents(query, top_k=5)
        if not matches:
            return {
                "draft": UNVERIFIED_RESPONSE,
                "sources": [],
                "verified_sources_available": False,
            }
        evidence = "\n\n".join(
            f"Official source: {item.get('metadata', {}).get('source_name', 'Official source')}\n"
            f"Title: {item.get('metadata', {}).get('document_title', 'Not specified')}\n"
            f"Evidence:\n{item['content']}"
            for item in matches
        )
        prompt = (
            "Prepare a clear, factual investor grievance complaint draft using only the case facts "
            "and official evidence below. Preserve names, amounts, dates, and events exactly as "
            "provided. Do not add legal conclusions, deadlines, eligibility claims, or facts that "
            "are not present. Mark missing details as [please provide]. Keep the draft suitable "
            "for the user to review and edit.\n\n"
            f"Case facts:\n{request.case.model_dump_json(indent=2)}\n\n"
            f"Official evidence:\n{evidence}"
        )
        draft = GeminiClient().generate_text(prompt, temperature=0.2)
        return {
            "draft": draft,
            "sources": _sources_from_matches(matches),
            "verified_sources_available": True,
        }
    except Exception as error:
        _raise_service_error(error)


@app.post("/api/complaint/pdf")
def create_complaint_pdf(request: PdfRequest) -> Any:
    from fastapi.responses import Response

    try:
        content = generate_pdf(request.content)
    except Exception as error:
        logger.error("complaint_pdf_generation_failed error_type=%s", type(error).__name__)
        raise HTTPException(status_code=422, detail="The draft contains text that could not be rendered in the PDF.") from error
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="sangyan-complaint-draft.pdf"'},
    )


@app.post("/api/iepf/guidance")
def iepf_guidance(request: IepfRequest) -> dict[str, Any]:
    try:
        retriever = Retriever()
        results = retriever.retrieve_relevant_documents(
            f"IEPF official guidance {request.question}",
            top_k=5,
        )
        if not results:
            return {
                "answer": UNVERIFIED_RESPONSE,
                "sources": [],
                "retrieved_count": 0,
                "gemini_called": False,
            }
        evidence = "\n\n".join(
            f"Official source: {item.get('metadata', {}).get('source_name', 'Official source')}\n"
            f"Evidence:\n{item['content']}"
            for item in results
        )
        answer = GeminiClient().generate_text(
            "Answer the user's IEPF question in concise, simple language. Use only the official "
            "evidence provided; if it does not support an answer, say so. Do not invent any "
            "procedure, deadline, or eligibility rule. Do not expose raw source chunks.\n"
            f"Language preference: {request.language}\n\nOfficial evidence:\n{evidence}\n\n"
            f"User question:\n{request.question}",
        )
        return {
            "answer": answer,
            "sources": _sources_from_matches(results),
        }
    except Exception as error:
        _raise_service_error(error)


@app.get("/api/sources")
def sources() -> dict[str, Any]:
    try:
        retriever = Retriever()
        collection = retriever.vector_store.collection
        registry = [item for item in _load_source_registry() if item.get("enabled", True)]
        output = []
        for source in registry:
            stored = collection.get(
                where={"source_id": source.get("id")},
                include=["metadatas"],
            )
            indexed = bool(stored.get("metadatas") or [])
            output.append(
                {
                    "id": source.get("id"),
                    "name": source.get("name"),
                    "url": source.get("url"),
                    "type": source.get("type", "official"),
                    "indexed": indexed,
                }
            )
        return {"sources": output}
    except Exception as error:
        _raise_service_error(error)


@app.get("/api/knowledge-base/status")
def knowledge_base_status() -> dict[str, Any]:
    if settings.app_env.lower() not in {"development", "test"}:
        raise HTTPException(status_code=404, detail="Not found.")
    try:
        return Retriever().vector_store.diagnostics()
    except Exception as error:
        _raise_service_error(error)