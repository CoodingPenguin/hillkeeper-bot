# CLAUDE.md

## Project Overview

**hillkeeper-bot** — Discord bot for managing weekly retrospective meeting attendance.
Small-scale (4 users), casual friend group, deployed on Render with Redis.

- **Tech**: Python 3.13+, discord.py 2.6+, Redis, Poetry
- **Architecture**: DDD — `attendance/`, `schedule/` domains with functional repository pattern

## Commands

```bash
poetry install                              # Install dependencies
poetry run python main.py                   # Run bot
poetry run pytest                           # Run tests
poetry run python -m py_compile <file>      # Syntax check
poetry run python scripts/send_notification.py morning|evening  # Manual test
```

## Project Structure

```
hillkeeper/
├── config.py              # Constants, env helpers
├── messages.py            # Embed templates
├── utils.py               # Discord utilities
├── attendance/            # Attendance domain (repository + service)
├── schedule/              # Schedule domain (repository + service)
├── database/redis.py      # Redis client singleton
└── bot/
    ├── commands.py        # Slash commands (incl. RescheduleGroup)
    ├── events.py          # Event handlers
    └── tasks.py           # Scheduled tasks (dynamic via Redis)
```

**Layer flow**: `bot/` → `domain/service.py` → `domain/repository.py` → `database/`

## Coding Conventions

### Python
- Python 3.13+ syntax: `T | None`, `set[T]`, `dict[K, V]` (not `typing.Optional` etc.)
- Keyword-only args with `*` for important parameters
- Functional repository pattern (module-level functions, not classes)
- Relative imports within package (`..config`, `. import repository`)

### Language
- **Docstrings**: English, Google Style, no type duplication in Args (types are in signature)
- **Log messages**: English
- **Comments**: English
- **User-facing messages (Discord embeds)**: Korean
- **Logger name**: always `'hillkeeper'`

### Import Order
1. Standard library
2. Third-party (`discord`, `redis`)
3. Internal modules (relative imports)

## Git Commit Rules

- **Always commit after completing work** — do not batch multiple tasks
- Group logically related changes in one commit
- For large tasks, commit intermediate steps
- Commit message format:

```
<Brief summary>

- Change 1
- Change 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Environment Variables

```bash
DISCORD_TOKEN, ATTENDANCE_CHANNEL_ID, RETROSPECTIVE_ROLE_ID
VOICE_CHANNEL_ID, REDIS_URL
TEST_CHANNEL_ID, TEST_ROLE_ID   # For test commands
```

## Redis Key Structure

```
attendance:event:{date}:{message_id}        # 7d TTL
attendance:response:{message_id}:{user_id}  # 7d TTL
schedule:default                             # No TTL (permanent)
schedule:override:{YYYY-MM-DD}              # 7d TTL
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/ping` | Check latency |
| `/schedule` | View current meeting schedule |
| `/reschedule once <day> <time>` | One-time change (this week) |
| `/reschedule default <day> <time>` | Permanent schedule change |
| `/reschedule skip` | Cancel this week's meeting |
| `/test_morning_check` | Test morning check (TEST_CHANNEL_ID) |
| `/test_evening_reminder` | Test evening reminder (TEST_CHANNEL_ID) |

## Adding a New Domain

Create `hillkeeper/<domain>/` with `repository.py` + `service.py`.
Follow the existing `attendance/` or `schedule/` patterns.

## Work Checklist

- Read files before editing
- Use `python -m py_compile` before committing
- Run `poetry run pytest` to verify no regressions
- Commit immediately after completing work
