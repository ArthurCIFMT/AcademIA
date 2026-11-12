import time
from collections.abc import Callable

import httpx
from pydantic import ValidationError

from app.modules.ai.adapters.groq import _SLOT
from app.modules.ai.orchestration.settings import Config, GeminiSettings
from app.modules.ai.ports.execution import ProviderError
from app.modules.ai.schemas.execution import Completion, Stage, Usage
from app.modules.ai.schemas.parsing import parse_object


class GeminiAdapter:
    def __init__(
        self,
        config: Config,
        settings: GeminiSettings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if config.provider != "gemini":
            raise ValueError("Provedor incompatível com adaptador Gemini.")
        self.config, self.settings, self.clock = (
            config,
            settings or GeminiSettings(),
            clock,
        )
        self._client = httpx.Client(
            transport=transport
            or httpx.HTTPTransport(
                proxy=self.settings.proxy_endpoint(),
                retries=0,
            ),
            trust_env=False,
            follow_redirects=False,
        )

    def close(self) -> None:
        self._client.close()

    def complete(
        self,
        messages: list[dict[str, str]],
        stage: Stage,
        output_tokens: int,
        timeout: float,
        on_dispatch: Callable[[], None],
    ) -> Completion:
        if not self.settings.api_key.get_secret_value():
            raise ProviderError("CREDENCIAL_AUSENTE")
        limit, stage_seconds = self.config.stage_limits(stage)
        if output_tokens != limit or timeout <= 0 or timeout > stage_seconds:
            raise ProviderError("LIMITE_INCOMPATIVEL")
        try:
            endpoint = self.settings.endpoint(self.config)
        except ValueError:
            raise ProviderError("CONFIGURACAO_INVALIDA") from None
        started = self.clock()
        if not _SLOT.acquire(timeout=timeout):
            raise ProviderError("TIMEOUT")
        try:
            remaining = timeout - (self.clock() - started)
            if remaining <= 0:
                raise ProviderError("TIMEOUT")
            if len(messages) != 2 or [m.get("role") for m in messages] != [
                "system",
                "user",
            ]:
                raise ProviderError("CONTEXTO_INCOMPATIVEL")
            body = {
                "systemInstruction": {"parts": [{"text": messages[0]["content"]}]},
                "contents": [
                    {"role": "user", "parts": [{"text": messages[1]["content"]}]}
                ],
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "candidateCount": 1,
                    "maxOutputTokens": output_tokens,
                    "responseMimeType": "application/json",
                    "thinkingConfig": {
                        "thinkingLevel": "minimal",
                        "includeThoughts": False,
                    },
                },
            }
            on_dispatch()
            with self._client.stream(
                "POST",
                endpoint,
                json=body,
                headers={
                    "x-goog-api-key": "" + self.settings.api_key.get_secret_value()
                },
                timeout=httpx.Timeout(remaining, connect=min(5, remaining)),
            ) as response:
                if response.status_code == 429:
                    raise ProviderError("QUOTA_EXCEDIDA")
                if response.status_code in {401, 403}:
                    raise ProviderError("CREDENCIAL_RECUSADA")
                if response.status_code != 200:
                    raise ProviderError("PROVEDOR_INDISPONIVEL")
                content = bytearray()
                for piece in response.iter_bytes():
                    content.extend(piece)
                    if len(content) > self.settings.max_response_bytes:
                        raise ProviderError("SAIDA_EXCEDIDA")
                    if self.clock() - started >= timeout:
                        raise ProviderError("TIMEOUT")
            if self.clock() - started >= timeout:
                raise ProviderError("TIMEOUT")
            data = parse_object(content.decode("utf-8"))
            if data.get("modelVersion") != self.config.model:
                raise ValueError("Modelo divergente.")
            choices = data["candidates"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError("Escolha inválida.")
            choice = choices[0]
            if not isinstance(choice, dict):
                raise ValueError("Escolha inválida.")
            if choice.get("finishReason") != "STOP":
                raise ProviderError("SAIDA_INTERROMPIDA")
            message = choice["content"]
            parts = message["parts"]
            if (
                message.get("role") != "model"
                or not isinstance(parts, list)
                or not parts
            ):
                raise ValueError("Mensagem inválida.")
            for part in parts:
                if (
                    not isinstance(part, dict)
                    or not isinstance(part.get("text"), str)
                    or part.get("thought")
                    or set(part) - {"text", "thought", "thoughtSignature"}
                ):
                    raise ValueError("Parte inválida ou ferramenta não autorizada.")
            usage = data.get("usageMetadata")
            parsed_usage = None
            if usage is not None:
                if not isinstance(usage, dict):
                    raise ValueError("Consumo inválido.")
                prompt = usage["promptTokenCount"]
                visible = usage.get("candidatesTokenCount", 0)
                thoughts = usage.get("thoughtsTokenCount", 0)
                if any(
                    type(v) is not int or v < 0 for v in (prompt, visible, thoughts)
                ):
                    raise ValueError("Consumo inválido.")
                parsed_usage = Usage.model_validate(
                    {
                        "prompt_tokens": prompt,
                        "completion_tokens": visible + thoughts,
                        "total_tokens": usage["totalTokenCount"],
                    }
                )
                if parsed_usage.completion_tokens > output_tokens:
                    raise ProviderError("CONSUMO_EXCEDIDO")
            return Completion(
                content="".join(p["text"] for p in parts), usage=parsed_usage
            )
        except httpx.TimeoutException:
            raise ProviderError("TIMEOUT") from None
        except httpx.TransportError:
            raise ProviderError("TRANSPORTE_INDISPONIVEL") from None
        except (ValueError, KeyError, TypeError, ValidationError):
            raise ProviderError("RESPOSTA_PROVEDOR_INVALIDA") from None
        finally:
            _SLOT.release()
