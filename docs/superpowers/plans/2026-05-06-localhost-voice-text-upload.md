# Localhost Voice Dropdown And Text Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a built-in voice dropdown and browser-side `.txt` upload to the Pocket TTS localhost page.

**Architecture:** Keep the current single-loaded-model FastAPI architecture. Expose lightweight `/voices` metadata from server constants, then let the frontend send the selected built-in voice through the existing `/tts` `voice_url` field. Text-file upload is fully client-side and fills the existing textarea.

**Tech Stack:** FastAPI, Typer, vanilla HTML/JavaScript, Tailwind classes, pytest.

---

## File Structure

- Modify `pocket_tts/main.py`: add a JSON endpoint that returns built-in voices, default voice, `max_tokens_per_chunk`, and a plain statement that no hard character limit exists.
- Modify `pocket_tts/static/index.html`: add a voice dropdown, keep custom voice URL as an advanced override, add `.txt` upload, add live character count, and update form submission priority.
- Add `tests/test_web_ui.py`: verify `/voices` metadata and that the root page contains the new controls.

### Task 1: Add Voice Metadata Endpoint

**Files:**
- Modify: `pocket_tts/main.py`
- Test: `tests/test_web_ui.py`

- [ ] **Step 1: Write the failing metadata test**

```python
from fastapi.testclient import TestClient

from pocket_tts.main import web_app


def test_voices_endpoint_returns_builtin_voice_metadata():
    client = TestClient(web_app)

    response = client.get("/voices")

    assert response.status_code == 200
    data = response.json()
    assert data["default_voice"] == "alba"
    assert data["max_tokens_per_chunk"] == 50
    assert data["hard_character_limit"] is None
    assert data["character_limit_note"] == (
        "No hard character limit is enforced; long text is split into tokenizer chunks."
    )
    assert {"name": "alba", "language": "en"} in data["voices"]
    assert {"name": "giovanni", "language": "it"} in data["voices"]
```

- [ ] **Step 2: Run the metadata test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_ui.py::test_voices_endpoint_returns_builtin_voice_metadata -q`

Expected: FAIL because `tests/test_web_ui.py` or `/voices` does not exist yet.

- [ ] **Step 3: Implement `/voices` metadata**

Add `BUILTIN_VOICE_LANGUAGES` near the server globals in `pocket_tts/main.py`:

```python
BUILTIN_VOICE_LANGUAGES = {
    "alba": "en",
    "anna": "en",
    "azelma": "en",
    "bill_boerst": "en",
    "caro_davy": "en",
    "charles": "en",
    "cosette": "en",
    "eponine": "en",
    "eve": "en",
    "fantine": "en",
    "george": "en",
    "jane": "en",
    "javert": "en",
    "jean": "en",
    "marius": "en",
    "mary": "en",
    "michael": "en",
    "paul": "en",
    "peter_yearsley": "en",
    "stuart_bell": "en",
    "vera": "en",
    "giovanni": "it",
    "lola": "es",
    "juergen": "de",
    "rafael": "pt",
    "estelle": "fr",
}
```

Add the endpoint after `/health`:

```python
@web_app.get("/voices")
async def voices():
    origin = str(tts_model.origin) if tts_model is not None else None
    default_voice = get_default_voice_for_language(origin)
    return {
        "default_voice": default_voice,
        "max_tokens_per_chunk": MAX_TOKEN_PER_CHUNK,
        "hard_character_limit": None,
        "character_limit_note": (
            "No hard character limit is enforced; long text is split into tokenizer chunks."
        ),
        "voices": [
            {"name": name, "language": BUILTIN_VOICE_LANGUAGES.get(name, "")}
            for name in sorted(_ORIGINS_OF_PREDEFINED_VOICES)
        ],
    }
```

- [ ] **Step 4: Run the metadata test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_ui.py::test_voices_endpoint_returns_builtin_voice_metadata -q`

Expected: PASS.

### Task 2: Add Frontend Controls

**Files:**
- Modify: `pocket_tts/static/index.html`
- Test: `tests/test_web_ui.py`

- [ ] **Step 1: Write the failing root-page test**

Append this test to `tests/test_web_ui.py`:

```python
def test_root_page_contains_voice_dropdown_and_text_upload_controls():
    client = TestClient(web_app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="voice-select"' in response.text
    assert 'id="text-file-input"' in response.text
    assert 'id="char-count"' in response.text
    assert "No hard character limit" in response.text
```

- [ ] **Step 2: Run the root-page test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_ui.py::test_root_page_contains_voice_dropdown_and_text_upload_controls -q`

Expected: FAIL because the new controls are not present yet.

- [ ] **Step 3: Add the frontend controls**

In `pocket_tts/static/index.html`, update the text panel to include:

```html
<div class="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
    <label class="inline-flex items-center gap-2 text-sm font-medium text-gray-700">
        <span>Upload .txt</span>
        <input
            type="file"
            id="text-file-input"
            class="block text-sm text-gray-700"
            accept=".txt,text/plain"
        />
    </label>
    <span id="char-count" class="text-xs text-gray-500">0 characters</span>
</div>
<p class="mt-2 text-xs text-gray-500">
    No hard character limit is enforced; long text is split into tokenizer chunks.
</p>
```

Replace the free-text voice URL panel with a built-in dropdown plus advanced URL:

```html
<div class="bg-white p-4 rounded-lg shadow">
    <label for="voice-select" class="block text-sm font-medium text-gray-700 mb-2">
        Built-in voice:
    </label>
    <select id="voice-select" class="w-full border rounded p-2"></select>
    <p id="voice-summary" class="text-xs text-gray-500 mt-1">
        Choose a built-in voice, or use the advanced URL/name override below.
    </p>

    <label for="voice-url-input" class="block text-sm font-medium text-gray-700 mt-4 mb-2">
        Advanced voice URL or name override:
    </label>
    <input
        type="text"
        id="voice-url-input"
        class="w-full border rounded p-2"
        placeholder="hf://kyutai/tts-voices/alba-mackenna/casual.wav"
    />
</div>
```

Add JavaScript references and handlers:

```javascript
const textFileInput = document.getElementById('text-file-input');
const charCount = document.getElementById('char-count');
const voiceSelect = document.getElementById('voice-select');
const voiceSummary = document.getElementById('voice-summary');

textInput.addEventListener('input', updateCharacterCount);
textFileInput.addEventListener('change', loadTextFile);

function updateCharacterCount() {
    const count = textInput.value.length;
    charCount.textContent = `${count.toLocaleString()} character${count === 1 ? '' : 's'}`;
}

async function loadTextFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    if (file.type && file.type !== 'text/plain') {
        showStatus('Please upload a plain .txt file.', false);
        event.target.value = '';
        return;
    }
    textInput.value = await file.text();
    updateCharacterCount();
    showStatus(`Loaded ${file.name}`, false);
    setTimeout(hideStatus, 3000);
}

async function loadVoices() {
    const response = await fetch(`${window.location.pathname.replace(/\/+$/, '')}/voices`);
    if (!response.ok) return;
    const data = await response.json();
    voiceSelect.innerHTML = '';
    for (const voice of data.voices) {
        const option = document.createElement('option');
        option.value = voice.name;
        option.textContent = voice.language ? `${voice.name} (${voice.language})` : voice.name;
        if (voice.name === data.default_voice) {
            option.selected = true;
        }
        voiceSelect.appendChild(option);
    }
    voiceSummary.textContent = `${data.voices.length} built-in voices. ${data.character_limit_note} Current chunk target: ${data.max_tokens_per_chunk} tokenizer tokens.`;
}
```

Update `generateAudio()` voice selection:

```javascript
const voiceUrl = document.getElementById('voice-url-input').value.trim();
const selectedVoice = voiceSelect.value;
const voiceWavFile = document.getElementById('voice-wav-input').files[0];

if (voiceWavFile) {
    formData.append('voice_wav', voiceWavFile);
} else if (voiceUrl) {
    formData.append('voice_url', voiceUrl);
} else if (selectedVoice) {
    formData.append('voice_url', selectedVoice);
}
```

Update the load handler:

```javascript
window.addEventListener('load', () => {
    textInput.focus();
    updateCharacterCount();
    loadVoices();
});
```

- [ ] **Step 4: Run root-page test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_ui.py -q`

Expected: PASS.

### Task 3: Verify Running Localhost

**Files:**
- Modify: none
- Test: browser and HTTP smoke

- [ ] **Step 1: Run targeted Python tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_ui.py -q`

Expected: `2 passed`.

- [ ] **Step 2: Restart the local server**

Stop the existing server processes if needed, then run:

```powershell
cd C:\Users\denko\Codex\pocket-tts
.\.venv\Scripts\pocket-tts.exe serve --host 0.0.0.0 --port 8000
```

Expected: Uvicorn reports it is running on port 8000.

- [ ] **Step 3: Verify HTTP metadata**

Run: `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/voices`

Expected: HTTP 200 and JSON containing `default_voice`, `voices`, and `max_tokens_per_chunk`.

- [ ] **Step 4: Verify in browser**

Open `http://localhost:8000/`.

Expected: the page shows the built-in voice dropdown, text-file upload, character counter, custom URL override, audio upload, and generate button.

## Self-Review

- Spec coverage: Built-in dropdown, text-file upload, and maximum-character answer are covered.
- Placeholder scan: No placeholder implementation steps remain.
- Type consistency: Endpoint fields match frontend and test names.
