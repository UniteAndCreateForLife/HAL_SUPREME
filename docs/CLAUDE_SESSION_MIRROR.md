# Claude Session Mirror for ChatGPT/HAL

## Purpose

Make parallel Claude Code sessions easy for HAL and ChatGPT to recover without relying on screenshots or manual copy/paste.

Claude Code already persists CLI transcripts locally. Anthropic documents the default transcript location as:

`~/.claude/projects/<project>/<session-id>.jsonl`

Claude hooks also receive `session_id` and `transcript_path`. The mirror uses those supported session identifiers and hook inputs, but treats the transcript JSONL itself as an opaque, version-unstable record.

## Private runtime output

The mirror writes only to:

`data/runtime/claude_session_mirror/`

This directory must remain local/private and must never be committed.

Files:

- `latest_sessions.md` — the first file ChatGPT/HAL should read.
- `index.json` — machine-readable recent-session index.
- `sessions/<session-id>/state.json` — last hook metadata and safe latest prompt/assistant text.
- `sessions/<session-id>/transcript.sanitized.jsonl` — a sanitized copy of the Claude transcript.

Common bearer tokens, API-key forms, JWT-like strings, token query parameters, and local home-directory prefixes are redacted before the ChatGPT-facing mirror is written.

## Install

From the HAL_SUPREME repository:

```powershell
D:\Python312\python.exe scripts\install_claude_session_mirror.py
```

The installer updates the **user-level** Claude settings at `~/.claude/settings.json` so parallel Desktop/CLI worktrees all receive the same mirror hook. It creates a timestamped backup before changing the file and adds hooks for:

- `UserPromptSubmit`
- `Stop`
- `PreCompact`
- `SessionEnd`

It also backfills up to 12 recent HAL_SUPREME Claude transcripts so currently open/recent sessions appear immediately.

## Why Stop is important

Claude's hook reference says transcript files are written asynchronously and can lag the in-memory turn. Stop hooks provide `last_assistant_message`, so the mirror stores that field directly instead of depending on the transcript copy to contain the newest assistant response.

## ChatGPT read path

Once the HAL ChatGPT Bridge is healthy, ChatGPT should read:

1. `data/runtime/claude_session_mirror/latest_sessions.md`
2. the chosen session's `state.json`
3. only then the sanitized transcript when deeper context is needed.

The bridge should expose only the sanitized mirror tree, never the original `~/.claude/projects` transcript location.

Recommended future bridge tools:

- `claude_sessions_list(limit=10)`
- `claude_session_state(session_id)`
- `claude_session_read(session_id, offset, limit)`

All three are read-only.

## Current-session behavior

After installation, a new user prompt and each normal Claude stop refresh the mirror automatically. The hook is filtered to HAL_SUPREME sessions so unrelated Claude projects are not copied into the ChatGPT-facing mirror. Existing open Claude Code sessions may need `/hooks`, a settings reload, or one new turn before the new hook configuration fires.

Do not put Claude account credentials, OAuth codes, passwords, or private connector URLs into prompts. The mirror is a continuity mechanism, not a secret store.
