# Claude Code Working Guidelines

This document defines the rules and context that Claude Code should follow when working on the hillkeeper-bot project.

## Project Overview

**hillkeeper-bot** is a Discord bot for managing attendance at weekly retrospective meetings.

### Key Features
- **Thursday 9:00 AM KST**: Send attendance check message mentioning `@회고` role with ✅/❌ emoji reactions
- **Thursday 9:45 PM KST**: Send reminder mentioning only participants who checked in

### Tech Stack
- Python 3.13+
- discord.py (Slash Commands)
- Redis (Render Key-Value Store)
- Poetry (dependency management)
- Deployment: Render

## Project Structure

```
hillkeeper-bot/
├── main.py                      # Entry point
├── hillkeeper/
│   ├── config.py               # Configuration + constants
│   ├── messages.py             # Message templates
│   ├── utils.py                # Discord utilities
│   ├── attendance/             # Attendance domain
│   │   ├── repository.py      # Data access (functional)
│   │   └── service.py         # Business logic
│   ├── database/               # Infrastructure
│   │   └── redis.py           # Redis client
│   └── bot/                    # Discord interface
│       ├── commands.py        # Slash commands
│       ├── events.py          # Event handlers
│       └── tasks.py           # Scheduled tasks
├── pyproject.toml
└── poetry.lock
```

### Architecture Principles

**Domain-Driven Design (DDD)**
- `attendance/`: Domain logic (repository + service)
- `database/`: Infrastructure layer (Redis connection)
- `bot/`: Interface layer (Discord)

**Layer Separation**
```
bot/ (Interface)
    ↓
attendance/service.py (Business Logic)
    ↓
attendance/repository.py (Data Access)
    ↓
database/redis.py (Infrastructure)
```

## Coding Style

### Python Version
- Use Python 3.13+ syntax
- `Optional[T]` → `T | None`
- `Set[T]` → `set[T]`
- `Dict[K, V]` → `dict[K, V]`

### Code Style
- **Docstrings**: Korean, ending with `~다.` (see Docstring Format below)
- **Log messages**: English
- **Logger name**: `'hillkeeper'` (unified)
- **Function parameters**: Use keyword-only args with `*` for important parameters
- **Comments**: Concise and clear, no separator lines like `====`

### Docstring Format

**Style**: Google Style (without type duplication)

**Format:**
```python
def function_name(param1: int, param2: str) -> bool:
    """
    함수의 간단한 설명입니다.
    추가 상세 설명이 필요한 경우 여기에 작성합니다.

    Args:
        param1: 첫 번째 파라미터 설명 (타입은 생략)
        param2: 두 번째 파라미터 설명

    Returns:
        반환값에 대한 설명

    Raises:
        ValueError: 예외 발생 조건
    """
```

**Key Points:**
- Opening `"""` 다음 줄바꿈
- 첫 줄: 간단한 요약 (한 문장)
- 상세 설명이 필요하면 빈 줄 후 추가 설명
- Args 섹션에는 **타입을 포함하지 않음** (type hints가 이미 시그니처에 있음)
- PyCharm/JetBrains IDE에서 Quick Documentation으로 보기 좋게 표시됨

**Rationale:**
- Type hints already in function signature → don't duplicate in Args
- Google Style Guide: "include required type(s) **if the code does not contain a corresponding type annotation**"
- PyCharm automatically generates Params from type hints + uses Args descriptions

### Import Style
```python
# Standard library
import logging
import datetime

# Third-party
import discord
from discord import app_commands

# Internal modules
from ..config import get_env
from . import repository
```

### Functional vs Class
- **Repository**: Functional (collection of functions, not class)
- **Client/Service**: Classes are acceptable, but prefer functional if simple

## Git Commit Rules

### 🔴 IMPORTANT: Always commit after making changes

**Principles:**
- Commit immediately after completing work
- Group logically related changes together
- For large tasks, commit intermediate steps

**Commit Message Format:**
```
<Title: Brief summary of what was done>

- Change 1
- Change 2
- Change 3

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example:**
```bash
git commit -m "$(cat <<'EOF'
Add Redis integration with functional repository pattern

- Created RedisClient for connection management
- Implemented functional repository for attendance data
- Updated service layer to use repository functions
- Added Redis initialization in main.py

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Environment Variables

### Required Variables
```bash
# Discord
DISCORD_TOKEN=your_token_here

# Channels & Roles
ATTENDANCE_CHANNEL_ID=channel_id
RETROSPECTIVE_ROLE_ID=role_id

# Redis (Render Key-Value Store)
REDIS_URL=redis://default:password@host:port

# Optional - for testing
TEST_CHANNEL_ID=test_channel_id
```

### Redis Configuration
- **Local development**: External URL + Allow all IPs (`0.0.0.0/0`)
- **Render deployment**: Internal URL (no IP restriction needed)

## Work Checklist

### Before Modifying Files
1. ✅ Read the file first (`Read` tool)
2. ✅ Consider concurrent editing (user might be editing too)

### When Writing Code
1. ✅ Use Python 3.13+ syntax
2. ✅ Korean docstrings (ending with `~다.`)
3. ✅ English log messages
4. ✅ Logger name: `'hillkeeper'`
5. ✅ Use relative imports (`..`, `.`)

### After Completion
1. ✅ Check syntax: `python -m py_compile`
2. ✅ **Commit immediately** 🔴
3. ✅ Write clear commit message describing changes

## Discord.py Patterns

### Slash Commands
```python
@bot.tree.command(name="command_name", description="Description")
async def command_name(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    # ... logic
    await interaction.followup.send("Message", ephemeral=True)
```

### Scheduled Tasks
```python
from discord.ext import tasks

@tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=KST))
async def my_task():
    # ... logic
```

### Event Handlers
```python
def register_events(bot):
    @bot.event
    async def on_ready():
        logger.info(f'Bot is ready: {bot.user}')

    @bot.event
    async def on_raw_reaction_add(payload):
        # Save user reactions to Redis
        ...
```

## Redis Patterns

### Data Storage Strategy
- **Storage Type**: Redis as primary storage (not just cache)
- **TTL**: 7 days (604800 seconds)
- **Reason**: Budget constraints, small scale (4 users)
- **Auto-cleanup**: Redis TTL handles expiration

### Key Structure
```redis
# Attendance event (7 days TTL)
attendance:event:{date}:{message_id}
  - message_id, channel_id, role_id, created_at

# User response (7 days TTL)
attendance:response:{message_id}:{user_id}
  - user_id, username, response (yes/no), timestamp
```

### Repository Pattern (Functional)
```python
# repository.py
TTL_7_DAYS = 604800

async def save_event(message_id: int, *, channel_id: int, role_id: int):
    date = datetime.now(KST).date()
    key = f"attendance:event:{date}:{message_id}"
    await redis_client.client.hset(key, mapping={...})
    await redis_client.client.expire(key, TTL_7_DAYS)

async def save_response(message_id: int, user_id: int, *, username: str, response: str):
    key = f"attendance:response:{message_id}:{user_id}"
    await redis_client.client.hset(key, mapping={...})
    await redis_client.client.expire(key, TTL_7_DAYS)

async def get_today_messages() -> list[int]:
    date = datetime.now(KST).date()
    pattern = f"attendance:event:{date}:*"
    # SCAN is fine for small scale (4 users)
    async for key in redis_client.client.scan_iter(match=pattern):
        ...
```

### Usage in Service Layer
```python
# service.py
from . import repository

# Save event
await repository.save_event(msg.id, channel_id=channel.id, role_id=int(role_id))

# Get today's messages
message_ids = await repository.get_today_messages()
```

### Event Handler Integration
```python
# events.py - Save user reactions to Redis
@bot.event
async def on_raw_reaction_add(payload):
    response = "yes" if str(payload.emoji) == EMOJI_CHECK else "no"
    await repository.save_response(
        payload.message_id,
        payload.user_id,
        username=member.display_name,
        response=response
    )
```

## Frequently Asked Questions

### Q: How to add a new domain?
A: Create a new folder under `hillkeeper/` (e.g., `voting/`)
```
hillkeeper/
├── voting/
│   ├── repository.py
│   └── service.py
```

### Q: How to add new infrastructure?
A: Add under `database/` (e.g., `postgresql.py`)

### Q: Why functional repository instead of class?
A: Simple project. Functions are more straightforward and have less boilerplate than classes.

### Q: Why no services/ folder? Why inside attendance/?
A: DDD pattern. Group repository + service together by domain.

## Important Notes

### ❌ DON'T
- Use old-style syntax like `typing.Optional`, `typing.Set`
- Write docstrings in English
- Write logs in Korean
- Make multiple changes without committing
- Edit files without reading them first

### ✅ DO
- Always read files before editing
- Commit immediately after completing work
- Check syntax before committing
- Write clear commit messages
- Think in terms of domains

## Updates

This document should be updated as the project evolves.
Please update this document whenever there are significant changes to conventions or architecture.
