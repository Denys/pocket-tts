"""Search chat-scoped repo memory by keyword and text."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MEMORY_PATH = REPO_ROOT / ".codex" / "interchat-memory.md"
MEMCPY_PATH = REPO_ROOT / ".codex" / "skills" / "memcpy" / "scripts" / "memcpy.py"


def load_memcpy_module():
    spec = importlib.util.spec_from_file_location("memcpy_skill_runtime", MEMCPY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load memcpy script from {MEMCPY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


memcpy = load_memcpy_module()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search memory entries scoped to one chat id.")
    parser.add_argument("--chat-id", required=True, help="Stable id for this chat/thread.")
    parser.add_argument(
        "--memory-file",
        type=Path,
        default=MEMORY_PATH,
        help="Memory file to read. Defaults to .codex/interchat-memory.md.",
    )
    parser.add_argument("--search", default="", help="Case-insensitive text search.")
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Keyword filter. May be repeated or comma-separated.",
    )
    parser.add_argument(
        "--list-keywords",
        action="store_true",
        help="List keywords for the selected chat and exit.",
    )
    parser.add_argument(
        "--around",
        type=int,
        default=1,
        help="Adjacent same-chat entries to include around each match.",
    )
    parser.add_argument("--limit", type=int, default=8, help="Maximum direct matches.")
    return parser.parse_args()


def entries_for_chat(content: str, chat_id: str) -> list[dict[str, str]]:
    return [entry for entry in memcpy.iter_memory_entries(content) if entry["chat_id"] == chat_id]


def entry_matches(entry: dict[str, str], query: str, keywords: list[str]) -> bool:
    normalized_query = query.lower().strip()
    normalized_keywords = set(memcpy.normalize_keywords(keywords))
    entry_keywords = set(entry["keywords"].split(",")) if entry["keywords"] else set()

    if normalized_keywords and not normalized_keywords.issubset(entry_keywords):
        return False
    if normalized_query and normalized_query not in entry["text"].lower():
        return False
    return bool(normalized_query or normalized_keywords)


def matching_indexes(
    entries: list[dict[str, str]], query: str, keywords: list[str], limit: int
) -> list[int]:
    indexes = [
        index for index, entry in enumerate(entries) if entry_matches(entry, query, keywords)
    ]
    return indexes[: max(1, limit)]


def expand_with_context(match_indexes: list[int], entry_count: int, around: int) -> list[int]:
    selected: set[int] = set()
    radius = max(0, around)
    for index in match_indexes:
        start = max(0, index - radius)
        end = min(entry_count, index + radius + 1)
        selected.update(range(start, end))
    return sorted(selected)


def format_results(entries: list[dict[str, str]], match_indexes: list[int], around: int) -> str:
    selected_indexes = expand_with_context(match_indexes, len(entries), around)
    match_set = set(match_indexes)
    blocks = []

    for index in selected_indexes:
        label = "MATCH" if index in match_set else "CONTEXT"
        blocks.append(f"### {label} {entries[index]['timestamp']}\n{entries[index]['text']}")

    return "\n\n".join(blocks)


def run_search(
    content: str,
    chat_id: str,
    query: str,
    keywords: list[str],
    around: int = 1,
    limit: int = 8,
) -> str:
    chat_id = memcpy.normalize_chat_id(chat_id)
    normalized_keywords = memcpy.normalize_keywords(keywords)
    entries = entries_for_chat(content, chat_id)
    indexes = matching_indexes(entries, query, normalized_keywords, limit)
    if not indexes:
        return f"No matches for chat {chat_id}."
    return format_results(entries, indexes, around)


def main() -> int:
    args = parse_args()

    try:
        chat_id = memcpy.normalize_chat_id(args.chat_id)
        keywords = memcpy.normalize_keywords(args.keyword)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    content = memcpy.ensure_memory_file(args.memory_file)

    if args.list_keywords:
        for keyword in memcpy.keywords_for_chat(content, chat_id):
            print(keyword)
        return 0

    if not args.search and not keywords:
        print("No search or keyword filter provided. Available keywords:")
        for keyword in memcpy.keywords_for_chat(content, chat_id):
            print(keyword)
        return 0

    print(
        run_search(
            content,
            chat_id=chat_id,
            query=args.search,
            keywords=keywords,
            around=args.around,
            limit=args.limit,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
