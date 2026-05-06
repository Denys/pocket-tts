"""Persist Codex compaction summaries into repo-local memory."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MEMORY_PATH = REPO_ROOT / ".codex" / "interchat-memory.md"
COMPACTION_HEADING = "## Compaction Events"
EMPTY_COMPACTION_TEXT = (
    "No compaction summaries have been recorded through "
    "`scripts/update_codex_memory.py` yet."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a Codex compaction summary to .codex/interchat-memory.md."
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        help="Path to a UTF-8 text file containing the compaction summary. Defaults to stdin.",
    )
    parser.add_argument(
        "--source",
        default="codex-compaction",
        help="Short source label stored with the memory entry.",
    )
    parser.add_argument(
        "--memory-file",
        type=Path,
        default=MEMORY_PATH,
        help="Memory file to update. Defaults to the repository memory file.",
    )
    return parser.parse_args()


def read_summary(summary_file: Path | None) -> str:
    if summary_file is None:
        summary = sys.stdin.read()
    else:
        summary = summary_file.read_text(encoding="utf-8")

    return summary.strip()


def ensure_memory_file(memory_file: Path) -> str:
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    if memory_file.exists():
        return memory_file.read_text(encoding="utf-8")

    initial_content = "\n".join(
        [
            "# Pocket TTS Interchat Memory",
            "",
            "Repository-local memory for Codex sessions.",
            "",
            COMPACTION_HEADING,
            "",
            EMPTY_COMPACTION_TEXT,
            "",
        ]
    )
    memory_file.write_text(initial_content, encoding="utf-8", newline="\n")
    return initial_content


def format_entry(summary: str, source: str, timestamp: dt.datetime | None = None) -> str:
    if timestamp is None:
        timestamp = dt.datetime.now(dt.timezone.utc)

    normalized_summary = "\n".join(line.rstrip() for line in summary.splitlines()).strip()
    indented_summary = "\n".join(
        f"  {line}" if line else "" for line in normalized_summary.splitlines()
    )
    timestamp_text = timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")

    return f"- {timestamp_text} `{source}`\n{indented_summary}\n"


def append_compaction_entry(content: str, entry: str) -> str:
    if COMPACTION_HEADING not in content:
        content = content.rstrip() + f"\n\n{COMPACTION_HEADING}\n\n"

    before, after = content.split(COMPACTION_HEADING, 1)
    body = after.lstrip("\n")

    if body.strip() == EMPTY_COMPACTION_TEXT:
        body = ""
    elif EMPTY_COMPACTION_TEXT in body:
        body = body.replace(EMPTY_COMPACTION_TEXT, "").lstrip("\n")

    updated_body = entry + ("\n" + body if body.strip() else "")
    return before.rstrip() + f"\n\n{COMPACTION_HEADING}\n\n" + updated_body.rstrip() + "\n"


def update_memory(memory_file: Path, summary: str, source: str) -> None:
    content = ensure_memory_file(memory_file)
    entry = format_entry(summary=summary, source=source)
    memory_file.write_text(append_compaction_entry(content, entry), encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    summary = read_summary(args.summary_file)
    if not summary:
        print("No summary provided; memory was not updated.", file=sys.stderr)
        return 1

    update_memory(memory_file=args.memory_file, summary=summary, source=args.source)
    print(f"Updated {args.memory_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
