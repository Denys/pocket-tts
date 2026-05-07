"""Tests for the local web UI and metadata endpoints."""

import re
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
                "specs": {"gender": "Female", "intonation": "Casual", "pitch": "Middle pitch"},
            },
            data["voices"],
        )
        self.assertIn(
            {
                "name": "giovanni",
                "language": "it",
                "specs": {"gender": "Male", "intonation": "Neutral", "pitch": "Lower pitch"},
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
        self.assertIn('id="experimental-mode-link"', response.text)
        self.assertIn('href="/glass"', response.text)
        self.assertIn("Experimental mode", response.text)
        self.assertIn('id="voice-select"', response.text)
        self.assertIn('id="preferred-voices"', response.text)
        self.assertIn('id="preferred-voice-toggle"', response.text)
        self.assertIn('id="voice-specs"', response.text)
        self.assertIn('id="voice-preview-btn"', response.text)
        self.assertIn('id="voice-preview-audio"', response.text)
        self.assertIn('id="silent-generate-input"', response.text)
        self.assertIn('id="download-progress"', response.text)
        self.assertIn('id="download-progress-bar"', response.text)
        self.assertIn('id="text-file-input"', response.text)
        self.assertIn('id="char-count"', response.text)
        self.assertIn("pocket-tts-preferred-voices", response.text)
        self.assertIn("readResponseBlobWithProgress", response.text)
        self.assertIn("setDownloadReady", response.text)
        self.assertIn("togglePreferredVoice", response.text)
        self.assertIn("removePreferredVoice", response.text)
        self.assertIn("renderPreferredVoices", response.text)
        self.assertIn("renderVoiceSpecs", response.text)
        self.assertIn("previewVoice", response.text)
        self.assertIn("Generate silently", response.text)
        self.assertIn("No hard character limit", response.text)

    def test_glass_page_serves_separate_modern_ui_without_replacing_root(self):
        previous_model = main.tts_model
        main.tts_model = types.SimpleNamespace(origin="english")
        try:
            client = TestClient(web_app)

            response = client.get("/glass")
            root_response = client.get("/")
        finally:
            main.tts_model = previous_model

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="glass-app"', response.text)
        self.assertIn('id="glass-voice-select"', response.text)
        self.assertIn('id="glass-preferred-voices"', response.text)
        self.assertIn('id="glass-preview-btn"', response.text)
        self.assertIn('id="glass-silent-generate-input"', response.text)
        self.assertIn('id="glass-playback-speed-select"', response.text)
        self.assertIn('id="glass-download-progress"', response.text)
        self.assertIn('id="glass-download-progress-bar"', response.text)
        self.assertIn('id="glass-generate-btn"', response.text)
        self.assertIn("Playback speed", response.text)
        self.assertIn("Download WAV is rendered at selected speed.", response.text)
        self.assertIn("pocket-tts-glass-playback-speed", response.text)
        self.assertIn("applyPlaybackSpeed", response.text)
        self.assertIn("renderSpeedAdjustedDownload", response.text)
        self.assertIn("encodeAudioBufferToWav", response.text)
        self.assertIn("readResponseBlobWithProgress", response.text)
        self.assertIn("setDownloadReady", response.text)
        self.assertIn("removePreferredVoice", response.text)
        self.assertIn("Generate silently", response.text)
        self.assertIn("glassmorphism", response.text)
        self.assertIn("Pocket TTS", root_response.text)
        self.assertNotIn('id="glass-app"', root_response.text)

    def test_glass_page_groups_controls_into_two_columns(self):
        previous_model = main.tts_model
        main.tts_model = types.SimpleNamespace(origin="english")
        try:
            client = TestClient(web_app)

            response = client.get("/glass")
        finally:
            main.tts_model = previous_model

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="glass-script-column"', response.text)
        self.assertIn('id="glass-voice-column"', response.text)
        self.assertIn('id="glass-script-card"', response.text)
        self.assertIn('id="glass-source-card"', response.text)
        self.assertIn('id="glass-voice-card"', response.text)
        self.assertIn('id="glass-generate-card"', response.text)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", response.text)
        self.assertRegex(
            response.text,
            re.compile(
                r'id="glass-script-column"[\s\S]*id="glass-script-card"'
                r"[\s\S]*id=\"glass-source-card\""
            ),
        )
        self.assertRegex(
            response.text,
            re.compile(
                r'id="glass-voice-column"[\s\S]*id="glass-voice-card"'
                r"[\s\S]*id=\"glass-generate-card\""
            ),
        )

    def test_glass_page_keeps_preview_next_to_preferred_with_accent_style(self):
        previous_model = main.tts_model
        main.tts_model = types.SimpleNamespace(origin="english")
        try:
            client = TestClient(web_app)

            response = client.get("/glass")
        finally:
            main.tts_model = previous_model

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.text,
            re.compile(
                r'id="glass-voice-actions"[\s\S]*id="glass-preferred-toggle"'
                r'[\s\S]*id="glass-preview-btn"'
            ),
        )
        self.assertRegex(
            response.text,
            re.compile(r'id="glass-preview-btn" class="button preview-accent"'),
        )


if __name__ == "__main__":
    unittest.main()
