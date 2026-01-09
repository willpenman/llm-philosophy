"""Run a single puzzle with the OpenAI adapter."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from src.runner import run_openai_puzzle  # noqa: E402


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _optional_path(value: str | None) -> Path | None:
    if value is None:
        return None
    return Path(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one puzzle against a single OpenAI model."
    )
    parser.add_argument("name", help="Puzzle name (filename without .py)")
    parser.add_argument("--model", default="o3-2025-04-16", help="Model snapshot name")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--special-settings", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _load_dotenv(ROOT / ".env")

    result = run_openai_puzzle(
        puzzle_name=args.name,
        model=args.model,
        max_output_tokens=args.max_output_tokens,
        temperature=args.temperature,
        seed=args.seed,
        special_settings=args.special_settings,
        dry_run=args.dry_run,
        puzzle_dir=_optional_path(args.puzzle_dir),
        system_path=_optional_path(args.system_path),
        responses_dir=_optional_path(args.responses_dir),
        api_key=args.api_key,
    )

    print(f"run_id={result.run_id}")
    print(f"request_path={result.request_path}")
    if result.response_text_path is None:
        print("response_text_path=None")
        return
    print(f"response_text_path={result.response_text_path}")
    print("\nOutput:\n")
    print(result.output_text)


if __name__ == "__main__":
    main()
