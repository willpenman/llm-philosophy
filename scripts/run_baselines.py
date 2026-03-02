"""Run baseline prompts for all models or a specific model.

Usage:
    python -m scripts.run_baselines --model claude-opus-4-6
    python -m scripts.run_baselines --model ALL
    python -m scripts.run_baselines --model ALL --providers anthropic openai
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from baselines.prompts import BASELINE_PROMPTS, BASELINE_SYSTEM_PROMPT, BaselinePrompt
from src.batch_runner import enumerate_all_models, filter_models, get_unreachable_models
from src.storage import utc_now_iso


ROOT = Path(__file__).resolve().parents[1]
BASELINES_DIR = ROOT / "baselines" / "responses"

# Min of max output tokens across providers (use model defaults, these are floors)
# Anthropic: 4000 (Haiku 3), OpenAI: 8192 (GPT-4), Gemini: 8192 (Flash Lite), Grok: 16384, Fireworks: 8192
DEFAULT_MAX_OUTPUT_TOKENS = 8192


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _get_provider_for_model(model: str) -> str | None:
    """Determine provider from model name."""
    from src.providers.anthropic import supports_model as anthropic_supports
    from src.providers.gemini import supports_model as gemini_supports
    from src.providers.grok import supports_model as grok_supports
    from src.providers.openai import supports_model as openai_supports
    from src.providers.fireworks import supports_model as fireworks_supports

    if anthropic_supports(model):
        return "anthropic"
    if openai_supports(model):
        return "openai"
    if gemini_supports(model):
        return "gemini"
    if grok_supports(model):
        return "grok"
    if fireworks_supports(model):
        return "fireworks"
    return None


def _run_baseline_anthropic(
    prompt: BaselinePrompt,
    model: str,
    api_key: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Run a baseline prompt with Anthropic."""
    from src.providers.anthropic import (
        build_messages_request,
        send_messages_request,
        require_api_key,
        default_thinking_config_for_model,
        supports_reasoning,
    )

    # Use thinking if available (same as eval)
    thinking = None
    if supports_reasoning(model):
        thinking = default_thinking_config_for_model(model)

    request = build_messages_request(
        system_prompt=BASELINE_SYSTEM_PROMPT,
        user_prompt=prompt.text,
        model=model,
        max_output_tokens=None,  # Use model default
        thinking=thinking,
        stream=False,
    )

    response = send_messages_request(
        request,
        api_key=api_key or require_api_key(),
    )

    output_text = response.output_text
    return output_text, response.payload


def _run_baseline_openai(
    prompt: BaselinePrompt,
    model: str,
    api_key: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Run a baseline prompt with OpenAI."""
    from src.providers.openai import (
        build_response_request,
        send_response_request,
        extract_output_text,
        require_api_key,
        default_reasoning_effort_for_model,
        supports_reasoning,
    )

    # Use reasoning if available (same as eval)
    reasoning = None
    if supports_reasoning(model):
        effort = default_reasoning_effort_for_model(model)
        if effort is not None:
            reasoning = {"effort": effort, "summary": "detailed"}

    request = build_response_request(
        system_prompt=BASELINE_SYSTEM_PROMPT,
        user_prompt=prompt.text,
        model=model,
        max_output_tokens=None,  # Use model default
        reasoning=reasoning,
        stream=False,
    )

    response = send_response_request(
        request,
        api_key=api_key or require_api_key(),
    )

    output_text = extract_output_text(response)
    return output_text, response


def _run_baseline_gemini(
    prompt: BaselinePrompt,
    model: str,
    api_key: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Run a baseline prompt with Gemini."""
    from src.providers.gemini import (
        build_generate_content_request,
        send_generate_content_request,
        require_api_key,
        supports_reasoning,
    )

    # Use thinking if available (same as eval)
    thinking_config = None
    if supports_reasoning(model):
        thinking_config = {"thinking_level": "HIGH", "include_thoughts": True}

    request = build_generate_content_request(
        system_prompt=BASELINE_SYSTEM_PROMPT,
        user_prompt=prompt.text,
        model=model,
        max_output_tokens=None,  # Use model default
        thinking_config=thinking_config,
    )

    response = send_generate_content_request(
        request,
        api_key=api_key or require_api_key(),
        stream=False,
    )

    return response.output_text, response.payload


def _run_baseline_grok(
    prompt: BaselinePrompt,
    model: str,
    api_key: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Run a baseline prompt with Grok."""
    from src.providers.grok import (
        build_chat_completion_request,
        send_chat_completion_request,
        extract_output_text,
        require_api_key,
    )

    # Grok reasoning models reason automatically without explicit config
    request = build_chat_completion_request(
        system_prompt=BASELINE_SYSTEM_PROMPT,
        user_prompt=prompt.text,
        model=model,
        max_output_tokens=None,  # Use model default
        stream=False,
    )

    response = send_chat_completion_request(
        request,
        api_key=api_key or require_api_key(),
    )

    output_text = extract_output_text(response)
    return output_text, response


def _run_baseline_fireworks(
    prompt: BaselinePrompt,
    model: str,
    api_key: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Run a baseline prompt with Fireworks."""
    from src.providers.fireworks import (
        build_chat_completion_request,
        send_chat_completion_request,
        extract_output_text,
        require_api_key,
        resolve_model,
    )

    model_id = resolve_model(model)

    request = build_chat_completion_request(
        system_prompt=BASELINE_SYSTEM_PROMPT,
        user_prompt=prompt.text,
        model=model_id,
        max_output_tokens=None,  # Use model default
        stream=False,
    )

    response = send_chat_completion_request(
        request,
        api_key=api_key or require_api_key(),
    )

    output_text = extract_output_text(response)
    return output_text, response


def run_baseline(
    prompt: BaselinePrompt,
    model: str,
    runner_provider: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Run a single baseline prompt and return output text and response."""
    runner_provider = runner_provider or _get_provider_for_model(model)

    if runner_provider == "anthropic":
        return _run_baseline_anthropic(prompt, model)
    elif runner_provider == "openai":
        return _run_baseline_openai(prompt, model)
    elif runner_provider == "gemini":
        return _run_baseline_gemini(prompt, model)
    elif runner_provider == "grok":
        return _run_baseline_grok(prompt, model)
    elif runner_provider == "fireworks":
        return _run_baseline_fireworks(prompt, model)
    else:
        raise ValueError(f"Unknown runner provider for model {model}")


def save_baseline_response(
    provider: str,
    model: str,
    prompt: BaselinePrompt,
    response_payload: dict[str, Any],
) -> Path:
    """Save baseline response to JSONL file."""
    model_dir = BASELINES_DIR / provider / model
    model_dir.mkdir(parents=True, exist_ok=True)

    responses_file = model_dir / "responses.jsonl"

    record = {
        "run_id": uuid4().hex,
        "created_at": utc_now_iso(),
        "provider": provider,
        "model": model,
        "prompt_name": prompt.name,
        "prompt_category": prompt.category,
        "prompt_text": prompt.text,
        "response": response_payload,
    }

    with responses_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.write("\n")

    return responses_file


def has_baseline_response(provider: str, model: str, prompt_name: str) -> bool:
    """Check if a baseline response already exists."""
    responses_file = BASELINES_DIR / provider / model / "responses.jsonl"
    if not responses_file.exists():
        return False

    with responses_file.open() as f:
        for line in f:
            try:
                record = json.loads(line)
                if record.get("prompt_name") == prompt_name:
                    return True
            except json.JSONDecodeError:
                continue

    return False


def run_all_baselines_for_model(
    model: str,
    storage_provider: str | None = None,
    runner_provider: str | None = None,
    resume: bool = True,
    dry_run: bool = False,
) -> None:
    """Run all baseline prompts for a single model."""
    # Determine runner provider (which API to call)
    runner_provider = runner_provider or _get_provider_for_model(model)
    if not runner_provider:
        print(f"Could not determine runner provider for {model}")
        return

    # Storage provider defaults to runner provider if not specified
    storage_provider = storage_provider or runner_provider

    print(f"\nRunning baselines for {model} ({storage_provider})")

    for prompt in BASELINE_PROMPTS:
        if resume and has_baseline_response(storage_provider, model, prompt.name):
            print(f"  [skip] {prompt.name} (already exists)")
            continue

        if dry_run:
            print(f"  [dry-run] {prompt.name}")
            continue

        try:
            print(f"  [run] {prompt.name}...", end=" ", flush=True)
            output_text, response = run_baseline(prompt, model, runner_provider)
            save_baseline_response(storage_provider, model, prompt, response)
            print(f"done ({len(output_text)} chars)")
        except Exception as e:
            print(f"ERROR: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run baseline prompts for models."
    )
    parser.add_argument(
        "--model",
        nargs="+",
        required=True,
        help="Model name(s), or ALL to run all models",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["openai", "gemini", "anthropic", "grok", "fireworks"],
        default=None,
        help="Filter to specific providers (when using ALL)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Skip prompts that already have responses (default: True)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Run all prompts even if responses exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually run, just show what would be done",
    )
    args = parser.parse_args()

    _load_dotenv(ROOT / ".env")

    resume = args.resume and not args.no_resume

    # Check if this is a batch run
    is_batch = "ALL" in args.model or len(args.model) > 1

    if is_batch:
        all_specs = enumerate_all_models()
        specs = filter_models(all_specs, args.model, args.providers)

        if not specs:
            print("No models match the specified filters.")
            return

        # Show unreachable models in dry-run mode
        if args.dry_run:
            unreachable = get_unreachable_models()
            if unreachable:
                print(f"\nNot running {len(unreachable)} unreachable models:")
                for spec in unreachable:
                    print(f"  - {spec.display_name} ({spec.provider}/{spec.model})")
                print()

        for spec in specs:
            run_all_baselines_for_model(
                model=spec.model,
                storage_provider=spec.provider,
                runner_provider=spec.runner_provider,
                resume=resume,
                dry_run=args.dry_run,
            )
    else:
        model = args.model[0]
        run_all_baselines_for_model(
            model=model,
            resume=resume,
            dry_run=args.dry_run,
        )

    print("\nDone!")


if __name__ == "__main__":
    main()
