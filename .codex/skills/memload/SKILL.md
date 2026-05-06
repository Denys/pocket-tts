---
name: memload
description: Use when the user asks to manually load repo memory into the current chat, force the agent to read memory, refresh project memory, or restore continuity from repo-local memory. Prefer memkw for specific retrieval before loading broad memory.
---

# Memload

Load repo-local memory into the current chat deliberately.

## Rule

Use a stable `--chat-id`. Default to same-chat memory plus repo-level static context. Do not
load all chats unless the user explicitly asks for full cross-chat memory.

## Workflow

1. If the user asks for a specific topic, use `memkw` first.
2. If the user asks to load memory generally, list keywords first:
   ```powershell
   uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <chat-id> --list-keywords
   ```
3. Load same-chat memory:
   ```powershell
   uv run python .codex/skills/memload/scripts/memload.py --chat-id <chat-id>
   ```
4. Read the command output into context and proceed from that state.

## Commands

Load current chat memory plus repo static memory sections:

```powershell
uv run python .codex/skills/memload/scripts/memload.py --chat-id <chat-id>
```

Load only the latest N same-chat entries:

```powershell
uv run python .codex/skills/memload/scripts/memload.py --chat-id <chat-id> --limit 3
```

Force full memory file load:

```powershell
uv run python .codex/skills/memload/scripts/memload.py --chat-id <chat-id> --full
```

Use `--full` only when the user explicitly asks for all repo memory; it can mix unrelated chats.
