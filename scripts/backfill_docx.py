"""Backfill .docx response files from existing response records."""

from __future__ import annotations

import json
from pathlib import Path

from src.puzzles import load_puzzle
from src.response_reader import (
    display_names,
    extract_input_text,
    extract_output_text,
)
from src.storage import (
    _format_display_date,
    _format_filename_timestamp,
    normalize_special_settings,
    write_response_docx,
)

ROOT = Path(__file__).resolve().parents[1]


def _docx_path(
    base_dir: Path,
    provider: str,
    model: str,
    model_display: str,
    puzzle_title: str,
    created_at: str,
) -> Path:
    """Generate path for docx file with human-readable filename.

    Format: "{Model} response - {Puzzle Title} {Timestamp}.docx"
    """
    timestamp = _format_filename_timestamp(created_at)
    filename = f"{model_display} response - {puzzle_title} {timestamp}.docx"
    return base_dir / provider / model / "texts" / filename


def backfill_from_jsonl(root: Path) -> int:
    count = 0
    for response_path in root.rglob("responses/*/*/responses.jsonl"):
        with response_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                provider = record.get("provider")
                model = record.get("model")
                puzzle_name = record.get("puzzle_name")
                puzzle_version = record.get("puzzle_version")
                created_at = record.get("created_at")
                special_settings = normalize_special_settings(
                    record.get("special_settings")
                )
                request_payload = record.get("request", {})
                response_payload = record.get("response", {})
                if not isinstance(provider, str) or not isinstance(model, str):
                    continue
                if not isinstance(puzzle_name, str) or not isinstance(created_at, str):
                    continue
                if not isinstance(request_payload, dict) or not isinstance(
                    response_payload, dict
                ):
                    continue

                system_text, user_text = extract_input_text(provider, request_payload)
                input_text = f"System\n{system_text}\n\nUser\n{user_text}"
                output_text = extract_output_text(provider, response_payload)

                puzzle = load_puzzle(puzzle_name, ROOT / "prompts" / "puzzles")
                display_name = puzzle.title or puzzle_name
                model_display, provider_display = display_names(provider, model)
                settings_display = (
                    ""
                    if normalize_special_settings(special_settings) == "default"
                    else f", {special_settings}"
                )
                puzzle_prefix = "Philosophy problem"
                display_date = _format_display_date(created_at)
                docx_path = _docx_path(
                    root / "responses",
                    provider,
                    model,
                    model_display,
                    display_name,
                    created_at,
                )
                docx_path.parent.mkdir(parents=True, exist_ok=True)
                write_response_docx(
                    path=docx_path,
                    puzzle_prefix=puzzle_prefix,
                    display_name=display_name,
                    puzzle_version=puzzle_version if isinstance(puzzle_version, str) else None,
                    model_display=model_display,
                    provider_display=provider_display,
                    settings_display=settings_display,
                    display_date=display_date,
                    input_text=input_text,
                    output_text=output_text,
                )
                count += 1
    return count


def main() -> None:
    total = backfill_from_jsonl(ROOT)
    print(f"Created {total} .docx files.")


if __name__ == "__main__":
    main()
