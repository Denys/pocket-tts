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
        self.assertIn({"name": "alba", "language": "en"}, data["voices"])
        self.assertIn({"name": "giovanni", "language": "it"}, data["voices"])

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
        self.assertIn('id="text-file-input"', response.text)
        self.assertIn('id="char-count"', response.text)
        self.assertIn("No hard character limit", response.text)


if __name__ == "__main__":
    unittest.main()
