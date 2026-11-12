import time
from collections.abc import Callable
from threading import BoundedSemaphore

import httpx
from pydantic import ValidationError

from app.modules.ai.orchestration.settings import Config, GroqSettings
from app.modules.ai.ports.execution import ProviderError
from app.modules.ai.schemas.execution import Completion, Stage, Usage
from app.modules.ai.schemas.parsing import parse_object

_SLOT = BoundedSemaphore(1)


class GroqAdapter:
    def __init__(
        self,
        config: Config,
        settings: GroqSettings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if config.provider != "groq":
            raise ValueError("Provedor incompatível com adaptador Groq.")
        self.config, self.settings, self.clock = (
            config,
            settings or GroqSettings(),
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
            body = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "reasoning_effort": self.config.reasoning_effort,
                "include_reasoning": self.config.include_reasoning,
                "response_format": {"type": "json_object"},
                "max_completion_tokens": output_tokens,
                "stream": False,
                "n": 1,
            }
            on_dispatch()
            with self._client.stream(
                "POST",
                endpoint,
                json=body,
                headers={
                    "Authorization": "Bearer "
                    + self.settings.api_key.get_secret_value()
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
            if data.get("model") != self.config.model:
                raise ValueError("Modelo divergente.")
            choices = data["choices"]
            if (
                not isinstance(choices, list)
                or len(choices) != 1
                or not isinstance(choices[0], dict)
            ):
                raise ValueError("Escolha inválida.")
            choice = choices[0]
            message = choice["message"]
            if choice.get("finish_reason") != "stop":
                raise ProviderError("SAIDA_INTERROMPIDA")
            if (
                not isinstance(message, dict)
                or message.get("role") != "assistant"
                or message.get("tool_calls")
                or message.get("function_call")
                or not isinstance(message.get("content"), str)
            ):
                raise ValueError("Mensagem inválida.")
            usage = data.get("usage")
            parsed_usage = None
            if usage is not None:
                if not isinstance(usage, dict):
                    raise ValueError("Consumo inválido.")
                parsed_usage = Usage.model_validate(
                    {
                        k: usage[k]
                        for k in ("prompt_tokens", "completion_tokens", "total_tokens")
                    }
                )
                if parsed_usage.completion_tokens > output_tokens:
                    raise ProviderError("CONSUMO_EXCEDIDO")
            return Completion(content=message["content"], usage=parsed_usage)
        except httpx.TimeoutException:
            raise ProviderError("TIMEOUT") from None
        except httpx.TransportError:
            raise ProviderError("TRANSPORTE_INDISPONIVEL") from None
        except (ValueError, KeyError, TypeError, ValidationError):
            raise ProviderError("RESPOSTA_PROVEDOR_INVALIDA") from None
        finally:
            _SLOT.release()
