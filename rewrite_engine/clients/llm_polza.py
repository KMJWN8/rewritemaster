# llm_polza.py
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # читает .env из текущей директории


class PolzaClient:
    """LLM client for Polza.ai, compatible with the existing LLMClient protocol."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ):
        api_key = api_key or os.environ["POLZA_AI_API_KEY"]
        self._model = model or os.environ.get(
            "POLZA_AI_MODEL", "google/gemini-2.5-flash-lite"
        )
        self._client = OpenAI(
            base_url="https://polza.ai/api/v1",
            api_key=api_key,
        )

    def complete(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=float(os.environ.get("POLZA_AI_TEMPERATURE", "0.3")),
            max_tokens=int(os.environ.get("POLZA_AI_MAX_TOKENS", "3000")),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""
