import datetime as dt
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MEMCPY_PATH = REPO_ROOT / ".codex" / "skills" / "memcpy" / "scripts" / "memcpy.py"
SPEC = importlib.util.spec_from_file_location("memcpy_skill", MEMCPY_PATH)
memcpy = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(memcpy)


class MemcpySkillTests(unittest.TestCase):
    def test_latest_entry_for_chat_ignores_newer_entries_from_other_chats(self):
        content = "\n".join(
            [
                "- Non-entry bullet with `backticks` must not parse as memory.",
                "",
                "## Compaction Events",
                "",
                "- 2026-05-06T13:20:00Z `memcpy`",
                "  [chat:chat-b] [previous:none] [keywords:other]",
                "  Other chat work.",
                "",
                "- 2026-05-06T13:10:00Z `memcpy`",
                "  [chat:chat-a] [previous:none] [keywords:ui, memory]",
                "  Current chat work.",
                "",
            ]
        )

        latest = memcpy.latest_entry_for_chat(content, "chat-a")

        self.assertIsNotNone(latest)
        self.assertEqual(latest["timestamp"], "2026-05-06T13:10:00Z")
        self.assertIn("Current chat work.", latest["body"])

    def test_append_memcpy_entry_links_to_previous_same_chat_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_file = Path(temp_dir) / ".codex" / "interchat-memory.md"
            first_time = dt.datetime(2026, 5, 6, 13, 10, tzinfo=dt.timezone.utc)
            second_time = dt.datetime(2026, 5, 6, 13, 20, tzinfo=dt.timezone.utc)

            memcpy.append_memcpy_entry(
                memory_file=memory_file,
                chat_id="chat-a",
                summary="First entry.",
                keywords=["memory"],
                timestamp=first_time,
            )
            memcpy.append_memcpy_entry(
                memory_file=memory_file,
                chat_id="chat-a",
                summary="Second entry.",
                keywords=["retrieval"],
                timestamp=second_time,
            )

            content = memory_file.read_text(encoding="utf-8")
            self.assertIn(
                "[chat:chat-a] [previous:2026-05-06T13:10:00Z] [keywords:retrieval]",
                content,
            )
            self.assertIn("Second entry.", content)

    def test_append_memcpy_entry_records_highlights(self):
        timestamp = dt.datetime(2026, 5, 6, 13, 30, tzinfo=dt.timezone.utc)

        entry = memcpy.format_memcpy_entry(
            summary="Detailed durable summary.",
            source="manual",
            chat_id="chat-a",
            previous_entry="none",
            keywords=["decision", "download-progress"],
            highlights=["Decision: keep /tts streaming and collect Blob client-side."],
            timestamp=timestamp,
        )

        self.assertIn("[keywords:decision, download-progress]", entry)
        self.assertIn("Highlights:", entry)
        self.assertIn(
            "- Decision: keep /tts streaming and collect Blob client-side.",
            entry,
        )

    def test_search_entries_is_scoped_by_chat_and_keyword(self):
        content = "\n".join(
            [
                "## Compaction Events",
                "",
                "- 2026-05-06T13:30:00Z `memcpy`",
                "  [chat:chat-b] [previous:none] [keywords:download-progress]",
                "  Other chat mentions download progress.",
                "",
                "- 2026-05-06T13:20:00Z `memcpy`",
                "  [chat:chat-a] [previous:none] [keywords:download-progress, ui]",
                "  Added download progress to classic mode.",
                "",
                "- 2026-05-06T13:10:00Z `memcpy`",
                "  [chat:chat-a] [previous:none] [keywords:memory]",
                "  Added memory tooling.",
                "",
            ]
        )

        matches = memcpy.search_entries(
            content,
            chat_id="chat-a",
            query="download progress",
            keywords=["download-progress"],
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["timestamp"], "2026-05-06T13:20:00Z")
        self.assertIn("classic mode", matches[0]["body"])

    def test_keywords_for_chat_lists_only_same_chat_keywords(self):
        content = "\n".join(
            [
                "## Compaction Events",
                "",
                "- 2026-05-06T13:20:00Z `memcpy`",
                "  [chat:chat-b] [previous:none] [keywords:foreign]",
                "  Other chat.",
                "",
                "- 2026-05-06T13:10:00Z `memcpy`",
                "  [chat:chat-a] [previous:none] [keywords:memory, ui]",
                "  Current chat.",
                "",
            ]
        )

        self.assertEqual(memcpy.keywords_for_chat(content, "chat-a"), ["memory", "ui"])

    def test_append_memcpy_entry_rejects_foreign_chat_tag_in_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_file = Path(temp_dir) / ".codex" / "interchat-memory.md"

            with self.assertRaises(ValueError):
                memcpy.append_memcpy_entry(
                    memory_file=memory_file,
                    chat_id="chat-a",
                    summary="[chat:chat-b] wrong thread.",
                )


if __name__ == "__main__":
    unittest.main()
