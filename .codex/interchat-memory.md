# Pocket TTS Interchat Memory

This file is the repository-local memory for Codex sessions. It is not platform memory and
does not depend on ChatGPT or Codex account-level memory settings.

## Update Contract

- Read this file before planning non-trivial work in this repository.
- After a Codex context compaction or thread resume, persist the supplied compaction summary
  here before continuing implementation work.
- Keep durable facts only: architecture decisions, feature state, known workflow constraints,
  validation commands, and unresolved risks.
- Do not store secrets, tokens, private credentials, personal data, or transient logs.
- Prefer updating existing bullets over appending duplicate facts.

## Current Product State

- Classic web UI is served from `/` by `pocket_tts/static/index.html`.
- Experimental glassmorphism web UI is served from `/glass` by `pocket_tts/static/glass.html`.
- Classic UI includes a button with `id="experimental-mode-link"` linking to `/glass`.
- `/voices` returns built-in voice metadata, selected voice specs, `preview_text`,
  `default_voice`, `character_limit_note`, and `max_tokens_per_chunk`.
- Both classic and glass UIs support voice preview, voice specs, preferred voices, text input,
  `.txt` upload, custom voice URL/name override, and uploaded reference audio.
- Preferred voices are browser-local and use localStorage key `pocket-tts-preferred-voices`.

## Workflow Constraints

- Running the local server on Windows can lock `.venv\Scripts\pocket-tts.exe`.
  Stop the listener on port `8000` before running tests that invoke `uv run`.
- Local development server command:
  `uv run pocket-tts serve --host 127.0.0.1 --port 8000`.
- Focused web UI checks:
  `uv run pytest tests/test_web_ui.py -v`.
- Focused lint check:
  `uvx ruff check pocket_tts/default_parameters.py pocket_tts/main.py tests/test_web_ui.py`.

## Compaction Events

- 2026-05-07T15:11:51Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-07T15:03:55Z] [keywords:glass-ui, playback-speed, download-wav, web-audio, tests]
  Highlights:
  - Action: /glass download link now renders a separate WAV Blob at the selected playback speed.
  - Decision: use browser Web Audio + OfflineAudioContext instead of backend speed support, which Pocket TTS still lacks.
  - Behavior: changing speed after generation re-renders the downloadable WAV from the stored original Blob.
  - Validation: focused web UI tests, Ruff, node --check, screenshot load, and health check passed.

  Updated /glass so the downloadable WAV reflects the selected playback speed. The generated TTS response is still collected as the original WAV Blob for the audio player, but the download link is now backed by a separate browser-rendered WAV Blob. For non-1.0x rates, createSpeedAdjustedWavBlob decodes the generated WAV with Web Audio, renders it through OfflineAudioContext using source.playbackRate, encodes the rendered AudioBuffer back to 16-bit PCM WAV via encodeAudioBufferToWav, and names the file with the selected speed such as pocket-tts-glass-1p25x.wav. Changing the speed after generation re-renders the download link from the stored original Blob.

  UI behavior: the download link is disabled while the speed-adjusted WAV is being prepared, the existing progress area says it is rendering the selected-speed WAV, and the active link text becomes "Download 1.25x WAV" for non-default rates. The audio preview/generated player also sets preservesPitch/mozPreservesPitch/webkitPreservesPitch false so the browser playback transform matches the rendered downloadable WAV semantics.

  Changed files: pocket_tts/static/glass.html and tests/test_web_ui.py. Validation passed: uv run pytest tests/test_web_ui.py -v; uvx ruff check tests/test_web_ui.py; extracted glass.html script passed node --check; Playwright screenshot loaded http://127.0.0.1:8000/glass at 1024x560; /health returned {"status":"healthy"}. A temporary Playwright unit-test attempt was not used for validation because this environment's npx runner could not resolve @playwright/test; generated test-results was removed.

- 2026-05-07T15:10:55Z `manual-chat-entry`
  [chat:pocket-tts-codex-voice-20260507] [previous:none] [keywords:codex-voice, pocket-tts, skill, plugin, hooks, tts, talk-speed]
  Highlights:
  - Decision: prefer an on-request Codex skill plus bundled script for Pocket TTS narration before building a plugin.
  - Action: scoped proposed voice-with-pocket-tts skill with voice, language, speed, output, play, and save options.
  - Risk: talk speed is not a native pocket-tts CLI parameter and should initially be implemented as audio post-processing.

  User asked whether pocket-tts can be connected to Codex to voice particularly long answers. Surface decision: for automatic post-answer speech, Codex local Stop hooks are the right mechanism because they can receive the final assistant message; MCP/plugin tooling would be on-demand rather than automatic. User then said an on-request workflow is acceptable and asked about a skill versus a plugin with voice selection, talk speed, saved audio, and selected-text voicing.

  Recommended v1: create a user-level Codex skill named voice-with-pocket-tts under C:\Users\Denys\.codex\skills\voice-with-pocket-tts with a bundled script scripts/voice_text.py. The skill should trigger on requests to voice/read/narrate selected text or an answer using Pocket TTS. The script should support stdin or --text-file, --voice, --language, --speed, --output, --play, and --save. Voice selection and WAV output are already supported by pocket-tts generate; talk speed should be implemented as post-processing because the current pocket-tts CLI does not expose a native speed/prosody-rate parameter. A plugin or MCP wrapper can be considered later only if UI controls, installable packaging, or richer tool affordances become worth the additional surface area.

  No files were created or changed in this thread. Pending next action is explicit approval to create the voice-with-pocket-tts skill and script.

- 2026-05-07T15:03:55Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-07T13:09:19Z] [keywords:glass-ui, playback-speed, tts-support, localstorage, tests]
  Highlights:
  - Decision: implement playback speed only because Pocket TTS has no native generation-time speed/pace parameter.
  - Action: add /glass playback speed selector applied to generated and preview audio via playbackRate.
  - Action: keep downloaded WAV timing unchanged and persist selected rate in localStorage.
  - Validation: focused web UI tests, Ruff, and 1024x560 Playwright screenshot passed.

  Added a /glass playback speed selector after checking that Pocket TTS does not expose a native model-level speech speed/pace parameter in TTSModel.generate_audio_stream or the /tts form endpoint. The selector is intentionally playback-only: it applies HTMLAudioElement defaultPlaybackRate/playbackRate to both generated audio and voice preview audio, persists the selected rate in localStorage key pocket-tts-glass-playback-speed, and keeps the downloaded WAV at original generated timing. The control offers 0.75x, 0.9x, 1.0x, 1.1x, 1.25x, and 1.5x.

  Layout adjustment for /glass: the speed selector sits beside Generate silently in the generate card. To keep the 1024x560 no-scroll glass layout from clipping controls, the previous lower metric pills are hidden and the important chunk target was moved into the Voice header as "26 voices / 50 token chunks". Rendered Playwright screenshot at 1024x560 confirmed the speed selector, generate button, preferred voice row, and chunk target fit in the viewport.

  Changed files: pocket_tts/static/glass.html and tests/test_web_ui.py. Validation passed: uv run pytest tests/test_web_ui.py -v; uvx ruff check tests/test_web_ui.py. The localhost server was restarted on http://127.0.0.1:8000 after validation.

- 2026-05-07T13:09:19Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-07T13:09:14Z] [keywords:windows-app, desktop, pywebview, server, tests, packaging]
  Highlights:
  - Decision: final Windows app uses embedded pywebview/WebView instead of opening the default browser
  - Action: app command now reuses healthy requested-port server and uses quiet Uvicorn logging
  - Action: build script creates iconed PyInstaller app and resyncs with desktop extra after packaging
  - Validation: desktop tests passed with 6 tests and app help passed with --extra desktop

  Since the prior same-chat checkpoint, the desktop app direction changed from browser-launcher to standalone Windows-compatible embedded UI. Added pocket_tts/desktop_app.py with DesktopAppOptions, port selection, /health waiting, existing-server reuse, quiet Uvicorn config, and embedded pywebview window launch. Added pocket_tts/windows_app.py as the GUI executable entry point and wired `pocket-tts app` in pocket_tts/main.py to call run_desktop_app. The final target does not open the user's default browser; it uses pywebview/WebView/WebView2 while still serving the existing FastAPI/HTML UI internally.

  Packaging workflow added: pyproject optional extras `desktop` and `build-windows`, gui script `pocket-tts-desktop`, scripts/create_windows_icon.py, scripts/build_windows_app.ps1, and docs/standalone-windows-app.md. The build script generates build/windows/Pocket-TTS.ico, runs PyInstaller windowed, writes dist/windows/Pocket TTS/, then resyncs the dev environment with only `--extra desktop` so later app launches do not uninstall build-only packages. README now documents `uvx --from "pocket-tts[desktop]" pocket-tts app` for installed use and `uv run --extra desktop pocket-tts app` for source checkouts.

  Debugged the noisy/repeated terminal behavior shown from Git Bash. Root causes: a separate `serve --host 127.0.0.1 --port 8000` process was occupying port 8000, `uv run pocket-tts app` was missing the desktop extra, and the first existing-server probe incorrectly used the full 120s startup timeout. Fixes: app reuses a healthy requested-port server instead of loading a second model, app uses `log_level="warning"` and `access_log=False`, and the preflight existing-server probe now uses a short 0.5s timeout before starting a new server. Added tests for busy-port handling, embedded WebView launch, missing pywebview error, existing-server reuse, short preflight probe, and Windows app entry point.

  Validation after these changes: `uv run pytest tests/test_desktop_app.py -v` passed with 6 tests; `uvx ruff check pocket_tts/desktop_app.py tests/test_desktop_app.py --fix` passed; `uv run --extra desktop pocket-tts app --help` passed. Earlier packaging validation produced dist/windows/Pocket TTS/Pocket TTS.exe and health checks for the launched app returned {"status":"healthy"}. Current workflow constraint remains: stop stale `serve` or app process trees on Windows before resyncing or relaunching if .venv/Scripts/pocket-tts.exe is locked.

- 2026-05-07T13:09:14Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-07T13:07:57Z] [keywords:glass-ui, voice-preview, layout, tests, codex-hooks, tts-integration]
  Highlights:
  - Action: refined /glass into explicit two-column grouping with Source under Script and generate controls under Voice
  - Action: moved Preview voice beside Add preferred and gave it a distinct accent style
  - Validation: focused web UI tests and Ruff for tests/test_web_ui.py passed
  - Decision: recommend a Codex Stop hook over MCP for deterministic long-answer voicing via pocket-tts

  After the 2026-05-07T13:07:57Z same-chat checkpoint, the glass UI was refined further. The /glass layout now uses two explicit columns: Script with Source underneath on the left, and Voice with the generate controls underneath on the right. The generate block was moved closer to the rest of the interface; Generate silently is grouped under Voice, and Source is grouped under Script. The Voice card now places Preview voice immediately to the right of Add preferred in a shared #glass-voice-actions row, with Preview voice styled using a distinct blue-teal .preview-accent button class.

  Tests were added/updated in tests/test_web_ui.py to pin the two-column grouping and the preview/preferred action-row grouping. Validation passed for the focused web UI suite: uv run pytest tests/test_web_ui.py -v, plus uvx ruff check tests/test_web_ui.py. Rendered browser validation on http://127.0.0.1:8000/glass confirmed the two-column grouping, the Preview voice accent button, and the preview panel opening after clicking Preview voice. A Tailwind CDN warning observed in browser logs was traced to the classic page index.html, not glass.html.

  OpenAI/Codex integration guidance was discussed but not implemented: for voicing particularly long Codex answers with pocket-tts, the recommended path is a Codex Stop hook that receives last_assistant_message, checks a character threshold, and invokes a local pocket-tts worker. pocket-tts already supports stdin input with pocket-tts generate --text - and the /tts HTTP endpoint streams WAV from form text. MCP was identified as less deterministic than a Stop hook for this use case because it depends on the model choosing to call a speak tool.

- 2026-05-07T13:07:57Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-06T13:38:56Z] [keywords:memory, memcpy, checkpoint]
  Highlights:
  - Event: user invoked memcpy on 2026-05-07.
  - State: no new code changes since the prior same-chat memory checkpoint.

  User explicitly invoked the repo-local memcpy skill on 2026-05-07. No code or memory-tooling changes were made after the prior same-chat checkpoint at 2026-05-06T13:38:56Z before this invocation. Current continuity state remains chat id pocket-tts-ui-20260506, with memory retrieval handled by memcpy for checkpoints, memkw for same-chat keyword search, and memload for same-chat memory loading.

- 2026-05-06T13:38:56Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-06T13:25:54Z] [keywords:memory, memload, memkw, retrieval]
  Highlights:
  - Decision: use memkw for targeted same-chat retrieval before memload.
  - Action: add memload and memkw repo-local skills with deterministic scripts.
  - Validation: 16 focused tests and Ruff passed.

  Created complementary repo-local memory loading skills: memkw and memload. memkw lists same-chat keywords and searches same-chat memory by text and/or keyword while including adjacent same-chat context via --around; it avoids loading the whole memory file for targeted questions. memload manually loads repo memory into the chat, defaulting to repo static memory plus same-chat entries only; --full exists for explicit full memory loads that may include unrelated chats. AGENTS.md now points future agents to memload for manual loading and memkw for targeted retrieval before broad loading. Added tests/test_memload_memkw_skill.py covering memkw adjacent context without cross-chat contamination and memload same-chat/static-context loading. Validation passed: uv run pytest tests/test_memload_memkw_skill.py tests/test_memcpy_skill.py tests/test_codex_memory.py tests/test_web_ui.py -v; uvx ruff check AGENTS.md .codex/skills/memcpy/scripts/memcpy.py .codex/skills/memkw/scripts/memkw.py .codex/skills/memload/scripts/memload.py tests/test_memload_memkw_skill.py tests/test_memcpy_skill.py scripts/update_codex_memory.py tests/test_codex_memory.py tests/test_web_ui.py.

- 2026-05-06T13:25:54Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-06T13:21:19Z] [keywords:memory, memcpy, retrieval, highlights]
  Highlights:
  - Decision: make memory entries self-indexing with keywords and highlights.
  - Action: add same-chat --search and --list-keywords commands.
  - Validation: 13 focused tests and Ruff passed.

  Updated repo-local memcpy retrieval model: entries now support [keywords:...] metadata and Highlights lines for important decisions, actions, events, validations, and risks. The memcpy parser now only recognizes timestamped memory entry headers, avoiding false positives from ordinary markdown bullets containing backticks. Added same-chat retrieval commands: --list-keywords and --search, both scoped by --chat-id; --search can be combined with --keyword and --limit. Updated .codex/skills/memcpy/SKILL.md with entry shape, keyword guidance, and retrieval commands. Updated AGENTS.md to require keywords/highlights for manual chat checkpoints. Added tests for highlight formatting, keyword listing, same-chat keyword search, and markdown-bullet parser safety.

- 2026-05-06T13:21:19Z `manual-chat-entry`
  [chat:pocket-tts-ui-20260506] [previous:2026-05-06T13:14:56Z]
  Created repo-local memcpy skill for chat-scoped memory checkpoints: .codex/skills/memcpy/SKILL.md and .codex/skills/memcpy/scripts/memcpy.py. The skill requires an explicit chat id, finds the latest prior entry with the same [chat:<id>] tag instead of using the global latest memory entry, writes [previous:<timestamp-or-none>] continuity pointers, rejects summaries containing a different chat tag, and documents manual commands for stdin or --summary-file. AGENTS.md now points future agents to the repo-local memcpy skill for manual chat checkpoints. Added tests/test_memcpy_skill.py covering same-chat lookup, previous-entry linking, and foreign-chat rejection. Validation passed: uv run pytest tests/test_memcpy_skill.py tests/test_codex_memory.py tests/test_web_ui.py -v; uvx ruff check AGENTS.md .codex/skills/memcpy/scripts/memcpy.py tests/test_memcpy_skill.py scripts/update_codex_memory.py tests/test_codex_memory.py tests/test_web_ui.py.

- 2026-05-06T13:14:56Z `manual-chat-entry`
  Manual checkpoint from prior memory entry through current request: added repo-local interchat memory support with .codex/interchat-memory.md, scripts/update_codex_memory.py, tests/test_codex_memory.py, and AGENTS.md instructions. Updated classic and glass web UIs after the checkpoint: classic / uses a compact viewport-fitting two-column layout; /glass uses a compact glassmorphism layout with visible Script, Voice, Source, silent toggle, and Generate controls at 1024x560. Both UIs now support Generate silently, removable preferred voice pills, download byte-progress indicators, and download buttons that stay inactive until the browser has collected the streamed WAV into a Blob. Web /tts still does not create a server-side output file; the browser creates an in-memory Blob/object URL for playback/download. Current validation repeatedly passed: uv run pytest tests/test_web_ui.py tests/test_codex_memory.py -v; uvx ruff check pocket_tts/default_parameters.py pocket_tts/main.py tests/test_web_ui.py scripts/update_codex_memory.py tests/test_codex_memory.py. Playwright screenshots were captured for / and /glass at 1024x560. Latest known server state before this entry: healthy on http://localhost:8000 with listener PID 30244.

- 2026-05-06T12:36:42Z `codex-compaction`
  Compaction resume captured prior Pocket TTS UI work: classic voice preview, voice specs, preferred voices, separate glassmorphism UI at /glass, classic Experimental mode link, and focused web UI tests. Validation commands used successfully: uv run pytest tests/test_web_ui.py -v; uvx ruff check pocket_tts/default_parameters.py pocket_tts/main.py tests/test_web_ui.py. Known Windows workflow constraint: stop port 8000 server before uv run when executable lock occurs.
