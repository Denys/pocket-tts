# Localhost Voice Dropdown And Text Upload Design

## Goal

Add a built-in voice selector and text-file upload to the existing Pocket TTS localhost
page without changing the model loading architecture.

## Current State

The FastAPI server loads one `TTSModel` at startup. The `/tts` endpoint accepts a `text`
form field and either `voice_url` or an uploaded `voice_wav`; uploaded audio takes
precedence. The frontend currently exposes a textarea, a custom voice URL input, and
an audio reference upload.

Pocket TTS does not define a hard character limit. It splits long text into chunks using
`MAX_TOKEN_PER_CHUNK = 50` tokenizer tokens. Practical limits are browser memory,
request size, generation time, server memory, and WAV response size.

## Approved Approach

Use a built-in voice dropdown for the current server language/model. Keep the existing
custom URL and audio-upload flows.

Priority order for voice selection:

1. Uploaded audio reference file.
2. Custom voice URL or voice name, when the advanced field is filled.
3. Built-in dropdown selection.

The page should read `.txt` files client-side and copy the content into the textarea.
It should show a character counter, but it should not enforce a hard character limit.

## Files

- `pocket_tts/main.py`: optionally expose built-in voices and text-limit metadata as JSON.
- `pocket_tts/static/index.html`: add voice dropdown, text-file upload, and character counter.
- `tests/test_web_ui.py`: cover the web page and metadata behavior.

## Validation

Run targeted tests for the web UI behavior, verify the CLI still imports, and restart the
localhost server before checking the page in the browser.
