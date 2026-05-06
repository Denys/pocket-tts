"""Append per-chat memory checkpoints without mixing unrelated chats."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MEMORY_PATH = REPO_ROOT / ".codex" / "interchat-memory.md"
CHAT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{1,79}$")
CHAT_TAG_RE = re.compile(r"\[chat:([A-Za-z0-9_.:-]+)\]")
ENTRY_HEADER_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z `[^`]+`")
KEYWORDS_TAG_RE = re.compile(r"\[keywords:([^\]]+)\]")
KEYWORD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$")

sys.path.insert(0, str(REPO_ROOT))

from scripts.update_codex_memory import append_compaction_entry, ensure_memory_file, format_entry  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a repo memory entry scoped to one explicit chat id."
    )
    parser.add_argument("--chat-id", required=True, help="Stable id for this chat/thread.")
    parser.add_argument(
        "--summary-file",
        type=Path,
        help="Path to a UTF-8 summary file. Defaults to stdin.",
    )
    parser.add_argument(
        "--source",
        default="memcpy",
        help="Short source label stored with the memory entry.",
    )
    parser.add_argument(
        "--memory-file",
        type=Path,
        default=MEMORY_PATH,
        help="Memory file to update. Defaults to .codex/interchat-memory.md.",
    )
    parser.add_argument(
        "--previous-entry",
        help="Explicit previous timestamp/id for bridging from an untagged entry.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Keyword tag. May be repeated or comma-separated.",
    )
    parser.add_argument(
        "--highlight",
        action="append",
        default=[],
        help="Important decision/action/event highlight. May be repeated.",
    )
    parser.add_argument(
        "--search",
        help="Search entries within the selected chat id and exit without writing.",
    )
    parser.add_argument(
        "--list-keywords",
        action="store_true",
        help="List keywords used by entries in the selected chat id and exit.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Maximum entries to print for --search.",
    )
    parser.add_argument(
        "--show-last",
        action="store_true",
        help="Print the latest entry for this chat id and exit without writing.",
    )
    return parser.parse_args()


def normalize_chat_id(chat_id: str) -> str:
    normalized = chat_id.strip()
    if not CHAT_ID_RE.fullmatch(normalized):
        raise ValueError(
            "chat id must be 2-80 chars: letters, digits, underscore, dot, colon, or hyphen"
        )
    return normalized


def normalize_keywords(raw_keywords: list[str] | None) -> list[str]:
    normalized_keywords: list[str] = []

    for raw_keyword in raw_keywords or []:
        for keyword in raw_keyword.split(","):
            normalized = keyword.strip().lower()
            if not normalized:
                continue
            if not KEYWORD_RE.fullmatch(normalized):
                raise ValueError(
                    "keywords must be 1-80 chars: letters, digits, underscore, dot, colon, "
                    "or hyphen"
                )
            if normalized not in normalized_keywords:
                normalized_keywords.append(normalized)

    return normalized_keywords


def normalize_highlights(raw_highlights: list[str] | None) -> list[str]:
    highlights = []
    for highlight in raw_highlights or []:
        normalized = " ".join(highlight.strip().split())
        if normalized and normalized not in highlights:
            highlights.append(normalized)
    return highlights


def read_summary(summary_file: Path | None) -> str:
    summary = sys.stdin.read() if summary_file is None else summary_file.read_text(encoding="utf-8")
    return summary.strip()


def iter_memory_entries(content: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: list[str] = []

    for line in content.splitlines():
        if ENTRY_HEADER_RE.match(line):
            if current:
                entries.append(parse_memory_entry(current))
            current = [line]
        elif current:
            current.append(line)

    if current:
        entries.append(parse_memory_entry(current))

    return entries


def parse_memory_entry(lines: list[str]) -> dict[str, str]:
    header = lines[0]
    timestamp = header[2:].split(" `", 1)[0].strip()
    body = "\n".join(lines[1:]).strip()
    chat_match = CHAT_TAG_RE.search(body)
    keywords_match = KEYWORDS_TAG_RE.search(body)
    keywords = []
    if keywords_match:
        keywords = normalize_keywords([keywords_match.group(1)])

    return {
        "timestamp": timestamp,
        "header": header,
        "body": body,
        "chat_id": chat_match.group(1) if chat_match else "",
        "keywords": ",".join(keywords),
        "text": "\n".join(lines),
    }


def latest_entry_for_chat(content: str, chat_id: str) -> dict[str, str] | None:
    for entry in iter_memory_entries(content):
        if entry["chat_id"] == chat_id:
            return entry
    return None


def keywords_for_chat(content: str, chat_id: str) -> list[str]:
    keywords: set[str] = set()
    for entry in iter_memory_entries(content):
        if entry["chat_id"] != chat_id:
            continue
        keywords.update(keyword for keyword in entry["keywords"].split(",") if keyword)
    return sorted(keywords)


def search_entries(
    content: str,
    chat_id: str,
    query: str | None = None,
    keywords: list[str] | None = None,
    limit: int = 8,
) -> list[dict[str, str]]:
    normalized_query = query.lower().strip() if query else ""
    normalized_keywords = set(normalize_keywords(keywords))
    matches = []

    for entry in iter_memory_entries(content):
        if entry["chat_id"] != chat_id:
            continue

        entry_keywords = set(entry["keywords"].split(",")) if entry["keywords"] else set()
        if normalized_keywords and not normalized_keywords.issubset(entry_keywords):
            continue
        if normalized_query and normalized_query not in entry["text"].lower():
            continue

        matches.append(entry)
        if len(matches) >= limit:
            break

    return matches


def validate_summary(summary: str, chat_id: str) -> None:
    for found_chat_id in CHAT_TAG_RE.findall(summary):
        if found_chat_id != chat_id:
            raise ValueError(
                f"summary contains [chat:{found_chat_id}], which does not match {chat_id}"
            )


def format_memcpy_entry(
    summary: str,
    source: str,
    chat_id: str,
    previous_entry: str | None,
    keywords: list[str] | None = None,
    highlights: list[str] | None = None,
    timestamp: dt.datetime | None = None,
) -> str:
    previous_text = previous_entry or "none"
    keyword_text = ", ".join(normalize_keywords(keywords) or ["checkpoint"])
    tagged_summary = f"[chat:{chat_id}] [previous:{previous_text}] [keywords:{keyword_text}]\n"

    normalized_highlights = normalize_highlights(highlights)
    if normalized_highlights:
        tagged_summary += "Highlights:\n"
        tagged_summary += "\n".join(f"- {highlight}" for highlight in normalized_highlights)
        tagged_summary += "\n\n"

    tagged_summary += summary.strip()
    return format_entry(tagged_summary, source, timestamp)


def append_memcpy_entry(
    memory_file: Path,
    chat_id: str,
    summary: str,
    source: str = "memcpy",
    previous_entry: str | None = None,
    keywords: list[str] | None = None,
    highlights: list[str] | None = None,
    timestamp: dt.datetime | None = None,
) -> dict[str, str] | None:
    chat_id = normalize_chat_id(chat_id)
    normalized_keywords = normalize_keywords(keywords)
    normalized_highlights = normalize_highlights(highlights)
    validate_summary(summary, chat_id)
    content = ensure_memory_file(memory_file)
    previous = latest_entry_for_chat(content, chat_id)
    previous_reference = previous_entry or (previous["timestamp"] if previous else None)
    entry = format_memcpy_entry(
        summary,
        source,
        chat_id,
        previous_reference,
        keywords=normalized_keywords,
        highlights=normalized_highlights,
        timestamp=timestamp,
    )
    memory_file.write_text(append_compaction_entry(content, entry), encoding="utf-8", newline="\n")
    return previous


def main() -> int:
    args = parse_args()

    try:
        chat_id = normalize_chat_id(args.chat_id)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    content = ensure_memory_file(args.memory_file)
    previous = latest_entry_for_chat(content, chat_id)

    try:
        keywords = normalize_keywords(args.keyword)
        highlights = normalize_highlights(args.highlight)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.show_last:
        if previous is None:
            print(f"No previous entry for chat {chat_id}.")
        else:
            print(previous["text"])
        return 0

    if args.list_keywords:
        for keyword in keywords_for_chat(content, chat_id):
            print(keyword)
        return 0

    if args.search is not None:
        matches = search_entries(
            content,
            chat_id=chat_id,
            query=args.search,
            keywords=keywords,
            limit=max(1, args.limit),
        )
        if not matches:
            print(f"No matches for chat {chat_id}.")
            return 0
        for match in matches:
            print(match["text"])
            print()
        return 0

    summary = read_summary(args.summary_file)
    if not summary:
        print("No summary provided; memory was not updated.", file=sys.stderr)
        return 1

    try:
        append_memcpy_entry(
            memory_file=args.memory_file,
            chat_id=chat_id,
            summary=summary,
            source=args.source,
            previous_entry=args.previous_entry,
            keywords=keywords,
            highlights=highlights,
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    previous_text = previous["timestamp"] if previous else args.previous_entry or "none"
    print(f"Updated {args.memory_file} for chat {chat_id}; previous={previous_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
