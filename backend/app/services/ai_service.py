"""Groq chat completion with strict Pydantic output validation."""

import json
import os
from typing import TypeVar

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, ValidationError

load_dotenv()
T = TypeVar("T", bound=BaseModel)


class AIServiceError(RuntimeError):
    """Raised for provider, parsing, or schema validation failures."""


def generate_structured(prompt: str, output_model: type[T]) -> T:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise AIServiceError("GROQ_API_KEY is not configured")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    try:
        client = Groq(api_key=api_key, timeout=45, max_retries=2)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return only valid JSON that conforms exactly to the requested schema. Do not invent evidence; cite only supplied source URLs."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        return output_model.model_validate(json.loads(raw))
    except (ValidationError, json.JSONDecodeError, IndexError, AttributeError) as exc:
        raise AIServiceError(f"Groq response did not match the required schema: {exc}") from exc
    except Exception as exc:
        raise AIServiceError(f"Groq request failed: {exc}") from exc
