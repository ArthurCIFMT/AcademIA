"""Provedor fixado na configuração: nenhuma troca por falha."""

from app.modules.ai.adapters.gemini import GeminiAdapter
from app.modules.ai.adapters.groq import GroqAdapter
from app.modules.ai.orchestration.settings import Config, GeminiSettings, GroqSettings


def credential_name(config: Config) -> str:
    return "GEMINI_API_KEY" if config.provider == "gemini" else "GROQ_API_KEY"


def create_adapter(config: Config) -> GroqAdapter | GeminiAdapter:
    if config.provider == "gemini":
        return GeminiAdapter(config, GeminiSettings())
    return GroqAdapter(config, GroqSettings())
