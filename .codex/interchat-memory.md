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
