from __future__ import annotations

import json
import re
from typing import TypeVar

import requests
from pydantic import BaseModel

from app.config.settings import get_settings

T = TypeVar("T", bound=BaseModel)


class LLMServiceError(RuntimeError):
    pass


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_available(self) -> bool:
        if self.settings.llm_mode == "mock":
            return True
        try:
            response = requests.get(f"{self.settings.ollama_base_url}/api/tags", timeout=3)
            return response.ok
        except requests.RequestException:
            return False

    def generate_json(self, prompt: str, output_model: type[T], system: str | None = None) -> T:
        if self.settings.llm_mode == "mock":
            raise LLMServiceError("Modo mock não produz extração generativa estruturada.")

        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "system": system or "Você é um analista especialista em apólices de seguro. Responda somente com dados sustentados pelo contexto.",
            "stream": False,
            "format": output_model.model_json_schema(),
            "options": {"temperature": 0.0},
        }
        try:
            response = requests.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json=payload,
                timeout=300,
            )
            response.raise_for_status()
            raw = response.json().get("response", "")
        except (requests.RequestException, ValueError) as exc:
            raise LLMServiceError(f"Falha ao chamar Ollama: {exc}") from exc

        raw = self._strip_fences(raw)
        try:
            return output_model.model_validate_json(raw)
        except Exception as exc:
            try:
                data = json.loads(raw)
                return output_model.model_validate(data)
            except Exception as nested:
                raise LLMServiceError(f"Resposta estruturada inválida do LLM: {nested}") from exc

    def generate_text(self, prompt: str, system: str | None = None) -> str:
        if self.settings.llm_mode == "mock":
            return "Resumo gerado em modo mock: comparação disponível na tabela estruturada."
        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "system": system or "Você é um analista especialista em seguros.",
            "stream": False,
            "options": {"temperature": 0.1},
        }
        try:
            response = requests.post(f"{self.settings.ollama_base_url}/api/generate", json=payload, timeout=300)
            response.raise_for_status()
            return str(response.json().get("response", "")).strip()
        except (requests.RequestException, ValueError) as exc:
            raise LLMServiceError(f"Falha ao chamar Ollama: {exc}") from exc

    @staticmethod
    def _strip_fences(value: str) -> str:
        value = value.strip()
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", value, flags=re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else value
