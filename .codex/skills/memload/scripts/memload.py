"""Load repo-local memory into chat context with same-chat scoping."""

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
    parser = argparse.ArgumentParser(description="Load repo memory scoped to one chat id.")
    parser.add_argument("--chat-id", required=True, help="Stable id for this chat/thread.")
    parser.add_argument(
        "--memory-file",
        type=Path,
        default=MEMORY_PATH,
        help="Memory file to read. Defaults to .codex/interchat-memory.md.",
    )
    parser.add_argument("--limit", type=int, help="Maximum same-chat entries to load.")
    parser.add_argument(
        "--no-static",
        action="store_true",
        help="Do not include repo-level memory sections before Compaction Events.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Print the complete memory file, including unrelated chats.",
    )
    return parser.parse_args()


def split_static_context(content: str) -> str:
    marker = "## Compaction Events"
    if marker not in content:
        return content.strip()
    return content.split(marker, 1)[0].rstrip()


def entries_for_chat(content: str, chat_id: str) -> list[dict[str, str]]:
    return [entry for entry in memcpy.iter_memory_entries(content) if entry["chat_id"] == chat_id]


def format_loaded_memory(
    content: str,
    chat_id: str,
    include_static: bool = True,
    limit: int | None = None,
) -> str:
    chat_id = memcpy.normalize_chat_id(chat_id)
    entries = entries_for_chat(content, chat_id)
    if limit is not None:
        entries = entries[: max(0, limit)]

    keywords = memcpy.keywords_for_chat(content, chat_id)
    sections = [
        "# Loaded Repo Memory",
        "",
        f"Chat: `{chat_id}`",
        f"Same-chat entries loaded: {len(entries)}",
        "",
        "## Keywords",
        "",
        "\n".join(f"- {keyword}" for keyword in keywords) if keywords else "No keywords found.",
    ]

    if include_static:
        sections.extend(["", "## Repo Static Memory", "", split_static_context(content)])

    sections.extend(["", "## Same-Chat Entries", ""])
    if entries:
        sections.append("\n\n".join(entry["text"] for entry in entries))
    else:
        sections.append(f"No entries found for chat `{chat_id}`.")

    return "\n".join(sections).rstrip() + "\n"


def main() -> int:
    args = parse_args()

    try:
        chat_id = memcpy.normalize_chat_id(args.chat_id)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    content = memcpy.ensure_memory_file(args.memory_file)
    if args.full:
        print(content.rstrip())
        return 0

    print(
        format_loaded_memory(
            content,
            chat_id=chat_id,
            include_static=not args.no_static,
            limit=args.limit,
        ).rstrip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
