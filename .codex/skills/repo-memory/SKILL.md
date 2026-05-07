---
name: repo-memory
description: Coordinate repo-local Codex memory workflows across memkw, memcpy, and memload. Use when the user asks to search, load, restore, continue from, checkpoint, save, summarize, audit, migrate, redact, export, or otherwise manage `.codex/interchat-memory.md`; preserve explicit source/target chat semantics, per-chat continuity, keyword/highlight retrieval, and no-secret memory hygiene.
---

# Repo Memory

Use this as the orchestrator for repo-local Codex memory. It routes to the existing
`memkw`, `memload`, and `memcpy` skills instead of replacing their scripts.

## Source And Target Semantics

Treat memory reads and writes differently:

- Read operations use a `source-chat-id`: the chat/thread whose memory should be searched or
  loaded into the current context. This can be the current chat, a previous chat, or a named
  continuity thread.
- Write operations use a `target-chat-id`: the current chat/thread that receives the new
  checkpoint. Prefer `$env:CODEX_THREAD_ID` when Codex exposes it.
- Do not default to the current chat id when the user asks to restore or continue earlier work.
  Identify the intended source chat first.
- Cross-chat loading is allowed when explicit. Cross-chat writing or continuity bridging needs a
  current-chat checkpoint with provenance.

## Route

Choose the narrowest action that fits:

- Specific topic, decision, file, command, keyword, or event: use `memkw` first.
- General restore or continuity load: list source keywords if ambiguous, then use `memload`.
- Manual checkpoint, chat-state save, or durable carry-forward summary: use `memcpy`.
- Codex compaction summary: use `scripts/update_codex_memory.py --source codex-compaction`.
- Unknown source chat, target chat, or write ownership: stop and ask for the missing id or scope.

## Preflight

Before any memory action:

1. Confirm the repo root contains `.codex/interchat-memory.md`.
2. Resolve source and target explicitly:
   - For reads: `source-chat-id`.
   - For writes: `target-chat-id`, usually `$env:CODEX_THREAD_ID`.
3. If the user only says "load memory", list source keywords before loading broad context.
4. Before writing, inspect the latest target-chat entry with `memcpy --show-last`.
5. For cross-chat carry-forward, load/search the source first, then write a new target-chat
   checkpoint that cites the source chat in a highlight.

## Safety Rules

- Do not use the global latest entry as continuity unless it has the same target chat id.
- Do not search or load all chats unless the user explicitly requests cross-chat memory.
- Do not store secrets, credentials, private personal data, raw transient logs, or full
  transcripts.
- Store durable facts only: feature state, decisions, actions, changed files, validations,
  constraints, risks, and unresolved next steps.
- Use stable noun keywords such as `memory`, `repo-memory`, `tests`, `server`,
  `download-progress`, or feature names. Avoid one-off prose fragments.
- Put retrieval-critical facts in `Highlights:` lines so future `memkw` searches can answer
  without loading the whole memory file.

## Command Patterns

List keywords for a source chat:

```powershell
uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <source-chat-id> --list-keywords
```

Search a source chat:

```powershell
uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <source-chat-id> --search "download progress" --around 1
```

Search by keyword:

```powershell
uv run python .codex/skills/memkw/scripts/memkw.py --chat-id <source-chat-id> --keyword download-progress --around 1
```

Load source-chat memory into the current context:

```powershell
uv run python .codex/skills/memload/scripts/memload.py --chat-id <source-chat-id>
```

Load only the latest source-chat entries:

```powershell
uv run python .codex/skills/memload/scripts/memload.py --chat-id <source-chat-id> --limit 3
```

Inspect latest target-chat checkpoint before writing:

```powershell
uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <target-chat-id> --show-last
```

Write a manual checkpoint:

```powershell
@'
Durable summary text.
'@ | uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <target-chat-id> --source manual-chat-entry --keyword memory --highlight "Decision: saved as repo-local memory"
```

Write a carry-forward checkpoint in a new chat after loading an old source:

```powershell
@'
Durable state carried forward from <source-chat-id>.
'@ | uv run python .codex/skills/memcpy/scripts/memcpy.py --chat-id <target-chat-id> --source manual-chat-entry --keyword continuity --highlight "Event: loaded source memory from <source-chat-id>"
```

Persist a Codex compaction summary:

```powershell
@'
Compaction summary containing durable facts only.
'@ | uv run python scripts/update_codex_memory.py --source codex-compaction
```

## Output Shape

When reporting memory work, include only the action and scope:

```text
Memory action: <search | load | checkpoint | compaction | bridge | audit>
Source chat: <id | none>
Target chat: <id | none>
Result: <loaded/searched/written/not found/not written>
Validation: <latest entry checked | keywords listed | command passed | not verified>
```

## Expansion Hooks

Keep these as future sub-skills or scripts only when repeated use shows enough friction:

- `memdoctor`: read-only health audit for malformed tags, missing chat ids, broken previous
  pointers, duplicate timestamps, invalid keywords, and cross-chat leakage hazards.
- `memcompact`: compaction-summary intake that strips transient material and persists durable facts.
- `memmigrate`: dry-run-first conversion of legacy or untagged entries into tagged per-chat form.
- `memredact`: scan and approval-gated redaction for secrets, credentials, private data, raw logs,
  or oversized transient dumps.
- `memexport`: portable handoff artifact for another chat or repo without dumping the full memory
  file.

Fold lightweight helpers into this skill until they need scripts:

- `mempreflight`: source/target id resolution, repo root check, keyword listing, and latest-entry
  inspection.
- `memsummarize`: memory-safe checkpoint drafting before `memcpy`.
- `memkeywords`: keyword normalization and highlight quality checks.

## Stop Conditions

Stop before writing if:

- no stable target chat id is available;
- source and target chat ids are confused;
- the requested operation would load or write all chats without explicit permission;
- the summary contains secrets, credentials, private personal data, raw logs, or transcript filler;
- a legacy migration, redaction, or repair would modify existing memory without a dry run and
  explicit approval.
