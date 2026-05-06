import datetime as dt
import tempfile
import unittest
from pathlib import Path

from scripts.update_codex_memory import append_compaction_entry, format_entry, update_memory


class CodexMemoryTests(unittest.TestCase):
    def test_format_entry_records_source_timestamp_and_summary(self):
        timestamp = dt.datetime(2026, 5, 6, 12, 30, tzinfo=dt.timezone.utc)

        entry = format_entry("Implemented feature\nVerified tests", "compaction", timestamp)

        self.assertIn("- 2026-05-06T12:30:00Z `compaction`", entry)
        self.assertIn("  Implemented feature", entry)
        self.assertIn("  Verified tests", entry)

    def test_append_compaction_entry_replaces_empty_placeholder(self):
        content = "\n".join(
            [
                "# Pocket TTS Interchat Memory",
                "",
                "## Compaction Events",
                "",
                "No compaction summaries have been recorded through "
                "`scripts/update_codex_memory.py` yet.",
                "",
            ]
        )

        updated = append_compaction_entry(content, "- entry\n  details\n")

        self.assertIn("## Compaction Events\n\n- entry\n  details", updated)
        self.assertNotIn("No compaction summaries have been recorded", updated)

    def test_update_memory_creates_file_and_appends_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_file = Path(temp_dir) / ".codex" / "interchat-memory.md"

            update_memory(memory_file, "Compacted current thread.", "test")

            content = memory_file.read_text(encoding="utf-8")
            self.assertIn("# Pocket TTS Interchat Memory", content)
            self.assertIn("`test`", content)
            self.assertIn("Compacted current thread.", content)


if __name__ == "__main__":
    unittest.main()
