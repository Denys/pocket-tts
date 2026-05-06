---
name: memcpy
description: Use when the user asks to save chat contents, make a memory checkpoint, copy current chat state to repo memory, or update interchat memory since the last entry while preserving per-chat continuity and avoiding mixing different chats.
---

# Memcpy

Save durable chat state into `.codex/interchat-memory.md` without mixing unrelated Codex chats.

## Core Rule

Never use the global latest memory entry as "last entry" unless it has the same chat id.
Continuity is per chat id. Every entry written by this skill must include `[chat:<id>]` and
a `[previous:<timestamp-or-none>]` pointer. Prefer every entry to also include
`[keywords:<keyword-list>]` and `Highlights:` lines for retrieval.

## Workflow

1. Read `.codex/interchat-memory.md`.
2. Determine the current chat id:
   - Prefer a stable platform/thread id if Codex exposes one.
   - Otherwise use an explicit human-readable id agreed in the chat.
   - If no stable id is known, ask for one before writing memory.
3. Inspect the latest same-chat entry:
   ```powershell
   uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --show-last
   ```
4. Summarize only durable facts since that same-chat entry:
   feature state, decisions, changed files, validation commands, known constraints, and risks.
5. Save the summary:
   ```powershell
   @'
   Durable summary since the last same-chat entry.
   '@ | uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --keyword ui --keyword tests --highlight "Decision: concise durable point"
   ```

## Entry Shape

Use retrieval-oriented metadata:

```text
[chat:<chat-id>] [previous:<timestamp-or-none>] [keywords:ui, memory, tests]
Highlights:
- Decision: important choice and reason.
- Action: concrete change made.
- Event: validation or state change.

Concise durable summary.
```

Good keywords are stable nouns or noun phrases: `download-progress`, `glass-ui`,
`classic-ui`, `memory`, `memcpy`, `tests`, `server`, `windows-lock`, `voice-preview`.
Avoid one-off prose fragments.

## Manual Command

Use `--source manual-chat-entry` for a user-requested checkpoint:

```powershell
@'
Durable summary text.
'@ | uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --source manual-chat-entry --keyword memory --highlight "Decision: saved as repo-local memory"
```

For a saved summary file:

```powershell
uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --source manual-chat-entry --summary-file path\to\summary.txt
```

## Retrieval Commands

Show last same-chat entry:

```powershell
uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --show-last
```

List keywords for one chat:

```powershell
uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --list-keywords
```

Search one chat by text:

```powershell
uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --search "download progress"
```

Search one chat by text and keyword:

```powershell
uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <chat-id> --search "Blob" --keyword download-progress
```

## Guardrails

- Do not store secrets, credentials, private personal data, or raw transient logs.
- Do not merge content from another chat just because it appears later in the memory file.
- If the last relevant entry is untagged but known to be this same chat, use
  `--previous-entry <timestamp>` once to bridge continuity into chat-tagged entries.
- Keep summaries concise and durable; do not paste full transcripts.
- Put decisions/actions/events in `--highlight` lines so future retrieval can answer targeted
  questions from search output instead of reading a whole chat transcript.
