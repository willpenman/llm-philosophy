"""Print the input and output of a stored response for a given model and puzzle."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.puzzles import load_puzzle
from src.response_reader import (
    display_names,
    extract_input_text,
    extract_output_text,
    find_response,
    format_response_plaintext,
)
from src.storage import _format_display_date, normalize_special_settings

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print a stored response for a given model and puzzle."
    )
    parser.add_argument("model", help="Model name (e.g., o3-2025-04-16)")
    parser.add_argument("puzzle", help="Puzzle name (filename without .py)")
    args = parser.parse_args()

    responses_dir = ROOT / "responses"
    record = find_response(responses_dir, args.model, args.puzzle)

    if record is None:
        print(f"No response found for model '{args.model}' and puzzle '{args.puzzle}'")
        return

    provider = record["provider"]
    model = record["model"]
    puzzle_name = record["puzzle_name"]
    puzzle_version = record.get("puzzle_version")
    created_at = record["created_at"]
    special_settings = normalize_special_settings(record.get("special_settings"))
    request_payload = record.get("request", {})
    response_payload = record.get("response", {})

    system_text, user_text = extract_input_text(provider, request_payload)
    input_text = f"System\n{system_text}\n\nUser\n{user_text}"
    output_text = extract_output_text(provider, response_payload)

    puzzle = load_puzzle(puzzle_name, ROOT / "prompts" / "puzzles")
    display_name = puzzle.title or puzzle_name
    model_display, provider_display = display_names(provider, model)
    settings_display = (
        ""
        if special_settings == "default"
        else f", {special_settings}"
    )
    display_date = _format_display_date(created_at)

    plaintext = format_response_plaintext(
        puzzle_prefix="Philosophy problem",
        display_name=display_name,
        puzzle_version=puzzle_version,
        model_display=model_display,
        provider_display=provider_display,
        settings_display=settings_display,
        display_date=display_date,
        input_text=input_text,
        output_text=output_text,
    )

    print(plaintext)


if __name__ == "__main__":
    main()
