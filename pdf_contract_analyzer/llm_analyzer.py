from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


PROMPT_TEMPLATE = """
Твоя задача — извлечь из текста договора номер, дату и предмет.
Текст может содержать OCR-ошибки, переносы строк, колонтитулы и повторяющиеся фрагменты.

Правила:
1) Номер договора:
   - Ищи рядом со словами: "ДОГОВОР", "КОНТРАКТ", "СОГЛАШЕНИЕ", "ДОПОЛНИТЕЛЬНОЕ СОГЛАШЕНИЕ"
   - Маркеры номера: "№", "N", "No", "номер"
   - Не путай с ИНН/КПП/ОГРН, банковскими счетами, телефонами, счетами/актами/накладными.
   - Верни номер так, как он написан (с символами / - буквами), можно с "№" если он есть в документе.

2) Дата договора:
   - Предпочтение дате заключения/подписания в шапке/титуле ("от …", "дата заключения …").
   - Если дата написана словами (например, "12 января 2024 г."), преобразуй в "12.01.2024" при уверенности.
   - Не выбирай даты сроков ("действует до", "срок", "по …") и даты приложений/актов.

3) Предмет:
   - Найди раздел "Предмет договора" / "1. Предмет" или похожее.
   - Сформулируй 1–2 предложения, кратко: что поставляется/какие услуги/работы, без лишних реквизитов.
   - Максимум 250–400 символов (по возможности).

Формат ответа:
- Верни ТОЛЬКО валидный JSON.
- Никакого Markdown, никаких комментариев, никаких пояснений.
- Если поле не найдено — значение "Не найдено".

JSON схема (строго эти ключи):
{
  "contract_number": "...",
  "contract_date": "...",
  "subject": "..."
}

Текст договора:
{extracted_text}
"""


@dataclass
class LlmResult:
    contract_number: str
    contract_date: str
    subject: str


class LlmAnalyzer:
    def __init__(self, provider: str, api_key: Optional[str], timeout: int = 30) -> None:
        self.provider = provider
        self.api_key = api_key
        self.timeout = timeout

    def analyze(self, text: str, max_chars: int) -> LlmResult:
        trimmed_text = text[:max_chars]
        prompt = PROMPT_TEMPLATE.format(extracted_text=trimmed_text)
        if self.provider == "gemini":
            response_text = self._call_gemini(prompt)
        elif self.provider == "openrouter":
            response_text = self._call_openrouter(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        data = self._safe_parse_json(response_text)
        if not data:
            raise ValueError("LLM returned invalid JSON")
        return LlmResult(
            contract_number=data.get("contract_number", "Не найдено"),
            contract_date=data.get("contract_date", "Не найдено"),
            subject=data.get("subject", "Не найдено"),
        )

    def _call_gemini(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError("google-generativeai is not installed") from exc

        genai.configure(api_key=self.api_key)
        generation_config = genai.GenerationConfig(temperature=0)
        model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

        for attempt in range(3):
            try:
                response = model.generate_content(
                    prompt,
                    request_options={"timeout": self.timeout},
                )
                return response.text or "{}"
            except Exception:  # pragma: no cover - external errors
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        return "{}"

    def _call_openrouter(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("requests is not installed") from exc
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "openrouter/auto",
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "You extract contract data."},
                {"role": "user", "content": prompt},
            ],
        }
        url = "https://openrouter.ai/api/v1/chat/completions"
        for attempt in range(3):
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            if response.status_code in {429, 500, 502, 503, 504}:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
        return "{}"

    def _safe_parse_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            json_text = self._extract_json_block(text)
            if not json_text:
                return {}
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                return {}

    @staticmethod
    def _extract_json_block(text: str) -> Optional[str]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start : end + 1]
