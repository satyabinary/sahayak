from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import TypeVar

from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel

from utils.config import settings
from utils.security.redaction import redact_sensitive_text

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiClientError(RuntimeError):
    pass

class GeminiRateLimitError(GeminiClientError):
    """Raised when the Gemini API rate limit or quota is exceeded."""

    def __init__(
        self,
        message: str,
        *,
        classification: str,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.classification = classification
        self.retry_after_seconds = retry_after_seconds


class GeminiClient:
    MAX_ATTEMPTS = 4
    MAX_RATE_LIMIT_RETRIES = 1
    _SECRET_ASSIGNMENT = re.compile(
        r"(?i)\b(api[_ -]?key|secret|access[_ -]?token|authorization)\b"
        r"\s*[:=]\s*[^\s,;]+"
    )

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model = settings.gemini_model
        self.embedding_model = settings.gemini_embedding_model
        self.client = genai.Client(api_key=self.api_key)

    def _sanitize_provider_message(self, message: str) -> str:
        sanitized = message
        if self.api_key:
            sanitized = sanitized.replace(self.api_key, "[REDACTED]")
        sanitized = self._SECRET_ASSIGNMENT.sub(r"\1=[REDACTED]", sanitized)
        return redact_sensitive_text(sanitized)[:500]

    @staticmethod
    def _retry_delay_from_value(value: object) -> float | None:
        if isinstance(value, (int, float)):
            return max(float(value), 0.0)
        if not isinstance(value, str):
            return None
        candidate = value.strip()
        try:
            return max(float(candidate), 0.0)
        except ValueError:
            pass
        duration_match = re.fullmatch(r"(\d+(?:\.\d+)?)s", candidate)
        if duration_match:
            return float(duration_match.group(1))
        try:
            retry_at = parsedate_to_datetime(candidate)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max((retry_at - datetime.now(timezone.utc)).total_seconds(), 0.0)

    @classmethod
    def _find_retry_delay(cls, error: Exception) -> float | None:
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", None)
        if headers:
            header_value = headers.get("Retry-After") or headers.get("retry-after")
            parsed = cls._retry_delay_from_value(header_value)
            if parsed is not None:
                return parsed

        def search(value: object) -> float | None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if str(key).lower().replace("-", "_") in {
                        "retryafter",
                        "retry_after",
                        "retrydelay",
                        "retry_delay",
                    }:
                        parsed_delay = cls._retry_delay_from_value(item)
                        if parsed_delay is not None:
                            return parsed_delay
                    nested = search(item)
                    if nested is not None:
                        return nested
            elif isinstance(value, list):
                for item in value:
                    nested = search(item)
                    if nested is not None:
                        return nested
            return None

        return search(getattr(error, "details", None))

    @staticmethod
    def _provider_error_fields(error: Exception) -> tuple[int | None, object, str, str]:
        response = getattr(error, "response", None)
        http_status = getattr(response, "status_code", None)
        if http_status is None:
            http_status = getattr(error, "code", getattr(error, "status_code", None))

        google_code: object = getattr(error, "code", None)
        google_status = getattr(error, "status", None)
        message = getattr(error, "message", None)
        details = getattr(error, "details", None)
        if isinstance(details, dict):
            nested = details.get("error", details)
            if isinstance(nested, dict):
                google_code = nested.get("code", google_code)
                google_status = nested.get("status", google_status)
                message = nested.get("message", message)
        return http_status, google_code, str(google_status or ""), str(message or "")

    @staticmethod
    def _classify_rate_limit(message: str, google_status: str, details: object) -> str:
        text = f"{message} {google_status} {details}".lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", text)
        if any(
            marker in normalized
            for marker in (
                "billing_account",
                "billing_is_disabled",
                "enable_billing",
                "billing_configuration",
                "payment_method",
                "billing_details",
            )
        ) and not any(
            marker in normalized
            for marker in (
                "exceeded_your_current_quota",
                "per_day",
                "daily_quota",
                "quota_exhausted",
                "quota_limit",
            )
        ):
            return "billing_configuration"
        if any(
            marker in normalized
            for marker in (
                "per_day",
                "daily_quota",
                "quota_exhausted",
                "exceeded_your_current_quota",
                "quota_limit",
                "per_project_per_day",
                "per_model_per_day",
                "freetier",
                "free_tier",
            )
        ):
            return "quota_exhausted"
        return "temporary_rate_limit"

    def _raise_rate_limit(self, operation: str, error: Exception) -> None:
        http_status, google_code, google_status, message = self._provider_error_fields(error)
        retry_after = self._find_retry_delay(error)
        classification = self._classify_rate_limit(
            message,
            google_status,
            getattr(error, "details", None),
        )
        safe_message = self._sanitize_provider_message(message or "No provider message supplied.")
        logger.warning(
            "gemini_429 operation=%s http_status=%s google_error_code=%s "
            "google_status=%s error_message=%r model=%s retry_after_seconds=%s "
            "classification=%s",
            operation,
            http_status,
            google_code,
            google_status or "unspecified",
            safe_message,
            self.model,
            retry_after,
            classification,
        )

        if classification == "quota_exhausted":
            user_message = (
                "Gemini quota or rate limit issue: the quota is exhausted for "
                "this project or model. "
                "Check the daily/project quota and try again after it resets."
            )
        elif classification == "billing_configuration":
            user_message = (
                "Gemini quota or rate limit issue: requests are blocked by a billing or quota configuration "
                "problem. Check billing and quota settings for the Google Cloud project."
            )
        elif retry_after is not None:
            user_message = (
                f"Gemini quota or rate limit issue: requests are temporarily rate-limited. Please try again in "
                f"{retry_after:g} seconds."
            )
        else:
            user_message = (
                "Gemini quota or rate limit issue: requests are temporarily "
                "rate-limited. Please wait briefly and try again."
            )
        raise GeminiRateLimitError(
            user_message,
            classification=classification,
            retry_after_seconds=retry_after,
        ) from error

    def _call_with_retry(self, operation: str, handler, *args, **kwargs):
        last_error: Exception | None = None
        rate_limit_retries = 0
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                logger.debug(
                    "gemini_request_started operation=%s model=%s attempt=%d",
                    operation,
                    self.model,
                    attempt + 1,
                )
                result = handler(*args, **kwargs)
                logger.debug(
                    "gemini_request_succeeded operation=%s model=%s attempt=%d",
                    operation,
                    self.model,
                    attempt + 1,
                )
                return result
            except Exception as exc:  # pragma: no branch
                last_error = exc
                status_code = getattr(exc, "code", getattr(exc, "status_code", None))
                if status_code == 429:
                    _, _, google_status, message = self._provider_error_fields(exc)
                    classification = self._classify_rate_limit(
                        message,
                        google_status,
                        getattr(exc, "details", None),
                    )
                    retry_after = self._find_retry_delay(exc)
                    if (
                        classification == "temporary_rate_limit"
                        and rate_limit_retries < self.MAX_RATE_LIMIT_RETRIES
                        and retry_after is not None
                    ):
                        rate_limit_retries += 1
                        logger.info(
                            "gemini_429_retry operation=%s model=%s retry_after_seconds=%s",
                            operation,
                            self.model,
                            retry_after,
                        )
                        time.sleep(retry_after)
                        continue
                    self._raise_rate_limit(operation, exc)
                logger.warning(
                    "gemini_request_failed operation=%s attempt=%d status=%s error_type=%s",
                    operation,
                    attempt + 1,
                    status_code,
                    type(exc).__name__,
                )
                if attempt + 1 < self.MAX_ATTEMPTS:
                    time.sleep(min(2 ** (attempt + 1), 8))
                    continue
        raise GeminiClientError(f"The AI service is currently unavailable while processing {operation}.") from last_error

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> str:
        if self.client is None:
            raise GeminiClientError("Gemini client could not be initialized. Check the API configuration.")
        output_token_limit = (
            settings.chat_max_output_tokens
            if max_output_tokens is None
            else max_output_tokens
        )

        def _execute() -> str:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=output_token_limit,
                    response_mime_type="text/plain",
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise GeminiClientError("The AI service did not return a useful text response.")
            return text

        return self._call_with_retry("text generation", _execute)

    def generate_json(self, prompt: str, model_cls: type[T]) -> T:
        if self.client is None:
            raise GeminiClientError("Gemini client could not be initialized. Check the API configuration.")

        def _execute() -> T:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=800,
                    response_mime_type="application/json",
                ),
            )
            raw = getattr(response, "text", None) or "{}"
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise GeminiClientError("The AI service returned malformed JSON.") from exc
            return model_cls.model_validate(parsed)

        return self._call_with_retry("structured output", _execute)

    def analyze_image(self, image_path: str, prompt: str) -> str:
        if self.client is None:
            raise GeminiClientError("Gemini client could not be initialized. Check the API configuration.")

        def _execute() -> str:
            with open(image_path, "rb") as image_file:
                uploaded = image_file.read()
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    genai_types.Part.from_bytes(
                        data=uploaded,
                        mime_type=(
                            "image/jpeg"
                            if image_path.lower().endswith((".jpg", ".jpeg"))
                            else "image/png"
                        ),
                    ),
                ],
                config=genai_types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=800,
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise GeminiClientError("The AI service could not inspect the uploaded image.")
            return text

        return self._call_with_retry("image analysis", _execute)

    def embed_text(self, text: str) -> list[float]:
        embeddings = self.embed_texts([text])
        return embeddings[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.client is None:
            raise GeminiClientError("Gemini embedding client could not be initialized. Check the API configuration.")
        if not texts:
            return []

        def _execute() -> list[list[float]]:
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=[
                    genai_types.Part.from_text(text=text)
                    for text in texts
                ],
            )
            values = getattr(result, "embeddings", None)
            if not values or len(values) != len(texts):
                raise GeminiClientError("The AI service did not return usable embeddings.")
            vectors: list[list[float]] = []
            for item in values:
                embedding = item.values if hasattr(item, "values") else item
                if not embedding:
                    raise GeminiClientError("The AI service returned malformed embedding data.")
                vectors.append(list(embedding))
            return vectors

        return self._call_with_retry("embedding generation", _execute)
