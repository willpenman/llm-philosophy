"""List available models grouped by provider."""

from __future__ import annotations

from collections import defaultdict
from src.providers.anthropic import (
    SUPPORTED_MODELS as ANTHROPIC_MODELS,
    display_model_name as display_anthropic_model_name,
    display_provider_name as display_anthropic_provider_name,
)
from src.providers.gemini import (
    SUPPORTED_MODELS as GEMINI_MODELS,
    display_model_name as display_gemini_model_name,
    display_provider_name as display_gemini_provider_name,
)
from src.providers.openai import (
    SUPPORTED_MODELS as OPENAI_MODELS,
    display_model_name as display_openai_model_name,
    display_provider_name as display_openai_provider_name,
)


def _format_model_name(model: str, display_name: str) -> str:
    if model == display_name:
        return model
    return f"{model} ({display_name})"


def main() -> None:
    grouped: dict[str, list[str]] = defaultdict(list)

    for model in sorted(OPENAI_MODELS):
        grouped[display_openai_provider_name("openai")].append(
            _format_model_name(model, display_openai_model_name(model))
        )

    for model in sorted(GEMINI_MODELS):
        grouped[display_gemini_provider_name("gemini")].append(
            _format_model_name(model, display_gemini_model_name(model))
        )

    for model in sorted(ANTHROPIC_MODELS):
        grouped[display_anthropic_provider_name("anthropic")].append(
            _format_model_name(model, display_anthropic_model_name(model))
        )

    for provider in sorted(grouped.keys()):
        print(provider)
        for model in grouped[provider]:
            print(f"- {model}")


if __name__ == "__main__":
    main()
