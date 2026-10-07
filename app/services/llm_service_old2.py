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
            "system": system
            or (
                "Você é um analista especialista em apólices de seguro. "
                "Responda somente com dados sustentados pelo contexto e no JSON solicitado."
            ),
            "stream": False,
            # Qwen3 suporta thinking. Para saídas estruturadas, desabilitamos o
            # thinking para garantir que o JSON final venha no campo `response`.
            "think": False,
            "format": output_model.model_json_schema(),
            "options": {
                "temperature": 0.0,
                # Evita respostas cortadas em extrações um pouco maiores.
                "num_predict": 8192,
            },
        }

        data = self._call_ollama(payload)
        raw = str(data.get("response") or "").strip()

        if not raw:
            thinking = str(data.get("thinking") or "")
            done_reason = data.get("done_reason") or data.get("done")
            raise LLMServiceError(
                "Ollama retornou HTTP 200, mas o campo 'response' veio vazio. "
                f"Modelo={self.settings.ollama_model!r}; "
                f"done_reason={done_reason!r}; thinking_chars={len(thinking)}. "
                "Verifique se o modelo está instalado e atualizado. Para Qwen3, "
                "mantenha 'think': false na chamada de geração estruturada."
            )

        raw = self._strip_fences(raw)
        try:
            return output_model.model_validate_json(raw)
        except Exception as exc:
            try:
                data_json = json.loads(raw)
                return output_model.model_validate(data_json)
            except Exception as nested:
                preview = raw[:1000].replace("\n", " ")
                raise LLMServiceError(
                    "Resposta estruturada inválida do LLM. "
                    f"Erro={nested}; início_da_resposta={preview!r}"
                ) from exc

    def generate_text(self, prompt: str, system: str | None = None) -> str:
        if self.settings.llm_mode == "mock":
            return "Resumo gerado em modo mock: comparação disponível na tabela estruturada."

        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "system": system or "Você é um analista especialista em seguros.",
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1, "num_predict": 4096},
        }
        data = self._call_ollama(payload)
        raw = str(data.get("response") or "").strip()
        if not raw:
            thinking = str(data.get("thinking") or "")
            raise LLMServiceError(
                "Ollama retornou resposta textual vazia. "
                f"Modelo={self.settings.ollama_model!r}; thinking_chars={len(thinking)}."
            )
        return raw

    def _call_ollama(self, payload: dict) -> dict:
        try:
            response = requests.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json=payload,
                timeout=300,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise LLMServiceError(
                    f"Resposta inesperada do Ollama: esperado objeto JSON, recebido {type(data).__name__}."
                )
            if data.get("error"):
                raise LLMServiceError(f"Ollama retornou erro: {data['error']}")
            return data
        except LLMServiceError:
            raise
        except requests.RequestException as exc:
            body = ""
            if getattr(exc, "response", None) is not None:
                body = (exc.response.text or "")[:1000]
            suffix = f" | corpo={body}" if body else ""
            raise LLMServiceError(f"Falha ao chamar Ollama: {exc}{suffix}") from exc
        except ValueError as exc:
            raise LLMServiceError(f"Ollama retornou conteúdo que não é JSON: {exc}") from exc

    @staticmethod
    def _strip_fences(value: str) -> str:
        value = value.strip()
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", value, flags=re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else value
