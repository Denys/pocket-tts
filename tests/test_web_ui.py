"""Tests for the local web UI and metadata endpoints."""

import types
import unittest

from fastapi.testclient import TestClient

import pocket_tts.main as main
from pocket_tts.main import web_app


class WebUiTests(unittest.TestCase):
    def test_voices_endpoint_returns_builtin_voice_metadata(self):
        client = TestClient(web_app)

        response = client.get("/voices")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["default_voice"], "alba")
        self.assertEqual(data["max_tokens_per_chunk"], 50)
        self.assertIsNone(data["hard_character_limit"])
        self.assertEqual(
            data["character_limit_note"],
            "No hard character limit is enforced; long text is split into tokenizer chunks.",
        )
        self.assertEqual(data["preview_text"], "Hello world.")
        self.assertIn(
            {
                "name": "alba",
                "language": "en",
                "specs": {
                    "gender": "Female",
                    "intonation": "Casual",
                    "pitch": "Middle pitch",
                },
            },
            data["voices"],
        )
        self.assertIn(
            {
                "name": "giovanni",
                "language": "it",
                "specs": {
                    "gender": "Male",
                    "intonation": "Neutral",
                    "pitch": "Lower pitch",
                },
            },
            data["voices"],
        )

    def test_voices_endpoint_returns_language_specific_preview_text(self):
        previous_model = main.tts_model
        main.tts_model = types.SimpleNamespace(origin="french_24l")
        try:
            client = TestClient(web_app)

            response = client.get("/voices")
        finally:
            main.tts_model = previous_model

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["preview_text"], "Bonjour le monde.")

    def test_root_page_contains_voice_dropdown_and_text_upload_controls(self):
        previous_model = main.tts_model
        main.tts_model = types.SimpleNamespace(origin="english")
        try:
            client = TestClient(web_app)

            response = client.get("/")
        finally:
            main.tts_model = previous_model

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="voice-select"', response.text)
        self.assertIn('id="preferred-voices"', response.text)
        self.assertIn('id="preferred-voice-toggle"', response.text)
        self.assertIn('id="voice-specs"', response.text)
        self.assertIn('id="voice-preview-btn"', response.text)
        self.assertIn('id="voice-preview-audio"', response.text)
        self.assertIn('id="text-file-input"', response.text)
        self.assertIn('id="char-count"', response.text)
        self.assertIn("pocket-tts-preferred-voices", response.text)
        self.assertIn("togglePreferredVoice", response.text)
        self.assertIn("renderPreferredVoices", response.text)
        self.assertIn("renderVoiceSpecs", response.text)
        self.assertIn("previewVoice", response.text)
        self.assertIn("No hard character limit", response.text)


if __name__ == "__main__":
    unittest.main()
