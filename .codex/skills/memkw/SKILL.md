---
name: memkw
description: Use when the user asks to search repo memory by keyword, list memory keywords, retrieve specific memory content, or find surrounding context without loading the whole memory file. Always scopes retrieval to one chat id.
---

# Memkw

Search `.codex/interchat-memory.md` without loading the whole memory file into context.

## Rule

Always use an explicit `--chat-id`. Do not search across all chats unless the user explicitly
asks for cross-chat memory.

## Commands

List available keywords for this chat:

```powershell
uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <chat-id> --list-keywords
```

Search text within this chat:

```powershell
uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <chat-id> --search "download progress"
```

Search by keyword and include adjacent same-chat context:

```powershell
uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <chat-id> --keyword download-progress --around 1
```

Search by text plus keyword:

```powershell
uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <chat-id> --search "Blob" --keyword download-progress --around 1
```

## Usage

- Start with `--list-keywords` when the user asks for memory but the target topic is vague.
- Use `--around 1` or `--around 2` when surrounding decisions or validation context matters.
- Prefer `memkw` before `memload` when a specific topic, decision, file, command, or event is requested.
