import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


memkw = load_module(
    "memkw_skill",
    REPO_ROOT / ".codex" / "skills" / "memkw" / "scripts" / "memkw.py",
)
memload = load_module(
    "memload_skill",
    REPO_ROOT / ".codex" / "skills" / "memload" / "scripts" / "memload.py",
)


class MemloadMemkwSkillTests(unittest.TestCase):
    def test_memkw_returns_match_with_adjacent_same_chat_context(self):
        content = "\n".join(
            [
                "## Compaction Events",
                "",
                "- 2026-05-06T13:30:00Z `memcpy`",
                "  [chat:chat-a] [previous:13:20] [keywords:download-progress]",
                "  Added Blob download progress.",
                "",
                "- 2026-05-06T13:20:00Z `memcpy`",
                "  [chat:chat-a] [previous:13:10] [keywords:memory]",
                "  Added memory checkpoint tooling.",
                "",
                "- 2026-05-06T13:10:00Z `memcpy`",
                "  [chat:chat-b] [previous:none] [keywords:download-progress]",
                "  Other chat Blob work.",
                "",
            ]
        )

        output = memkw.run_search(
            content,
            chat_id="chat-a",
            query="Blob",
            keywords=["download-progress"],
            around=1,
        )

        self.assertIn("### MATCH 2026-05-06T13:30:00Z", output)
        self.assertIn("### CONTEXT 2026-05-06T13:20:00Z", output)
        self.assertNotIn("Other chat Blob work.", output)

    def test_memload_includes_static_context_and_only_same_chat_entries(self):
        content = "\n".join(
            [
                "# Pocket TTS Interchat Memory",
                "",
                "## Workflow Constraints",
                "",
                "- Stop port 8000 before uv run.",
                "",
                "## Compaction Events",
                "",
                "- 2026-05-06T13:30:00Z `memcpy`",
                "  [chat:chat-a] [previous:none] [keywords:memory]",
                "  Same chat entry.",
                "",
                "- 2026-05-06T13:20:00Z `memcpy`",
                "  [chat:chat-b] [previous:none] [keywords:foreign]",
                "  Foreign chat entry.",
                "",
            ]
        )

        output = memload.format_loaded_memory(content, chat_id="chat-a")

        self.assertIn("## Repo Static Memory", output)
        self.assertIn("Stop port 8000 before uv run.", output)
        self.assertIn("Same chat entry.", output)
        self.assertNotIn("Foreign chat entry.", output)


if __name__ == "__main__":
    unittest.main()
