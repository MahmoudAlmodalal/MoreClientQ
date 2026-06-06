import asyncio
import logging
from openai import AsyncOpenAI, APIStatusError
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMUnavailableError(Exception):
    """Custom exception raised when the LLM service is unavailable."""
    pass

# Initialize client using LLM_TIMEOUT_SECONDS configuration
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY or "dummy_key",
    timeout=float(settings.LLM_TIMEOUT_SECONDS)
)

async def complete(messages: list, model: str, stream: bool = False):
    """
    Call AsyncOpenAI with the given model.
    On APIStatusError (429/503) or asyncio.TimeoutError, raises LLMUnavailableError.
    """
    try:
        return await client.chat.completions.create(
            messages=messages,
            model=model,
            stream=stream
        )
    except APIStatusError as e:
        logger.warning(f"OpenAI API error {e.status_code} for model {model}: {e}")
        # Treat all provider-side HTTP errors as unavailability so the
        # complete_with_fallback chain can always attempt the secondary model.
        # 429 = rate-limited, 503 = overloaded, 500/502 = transient server error.
        raise LLMUnavailableError(f"LLM service error (HTTP {e.status_code}): {e}")
    except asyncio.TimeoutError as e:
        logger.warning(f"OpenAI API timeout for model {model}: {e}")
        raise LLMUnavailableError("LLM request timed out")
    except Exception as e:
        logger.error(f"Unexpected OpenAI error for model {model}: {e}")
        raise e

async def complete_with_fallback(messages: list, stream: bool = False):
    """
    Try LLM_PRIMARY_MODEL first; on failure, try LLM_FALLBACK_MODEL.
    On double failure, raises LLMUnavailableError.
    """
    try:
        return await complete(messages, model=settings.LLM_PRIMARY_MODEL, stream=stream)
    except LLMUnavailableError as e:
        logger.warning(f"Primary model {settings.LLM_PRIMARY_MODEL} unavailable. Retrying with fallback: {e}")
        try:
            return await complete(messages, model=settings.LLM_FALLBACK_MODEL, stream=stream)
        except LLMUnavailableError as fallback_err:
            logger.error(f"Fallback model {settings.LLM_FALLBACK_MODEL} also failed: {fallback_err}")
            raise LLMUnavailableError("Both primary and fallback LLM models are unavailable.")
