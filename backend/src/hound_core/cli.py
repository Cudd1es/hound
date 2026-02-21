"""Local CLI entrypoint for job posting analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .service import analyze_posting


def run_analysis(resume_path: Path, posting_path: Path) -> dict[str, Any]:
    profile = json.loads(resume_path.read_text(encoding="utf-8"))
    posting_text = posting_path.read_text(encoding="utf-8")
    return analyze_posting(profile=profile, posting_text=posting_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze resume fit for a job posting.")
    parser.add_argument("--resume", required=True, type=Path, help="Path to resume JSON file.")
    parser.add_argument("--posting", required=True, type=Path, help="Path to job posting text file.")
    parser.add_argument("--output", type=Path, help="Optional output path for JSON report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    report = run_analysis(resume_path=args.resume, posting_path=args.posting)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
