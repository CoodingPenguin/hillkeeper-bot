# Hillkeeper Bot

A Discord bot that automates attendance tracking for a small friend group's biweekly retrospective meetings.

## Why

Our AC2 alumni group holds a weekly retrospective. Before this bot, someone had to manually ask "who's coming tonight?" and chase people for responses. Hillkeeper automates the entire flow — morning roll call, response tracking, and evening reminder — so no one has to play secretary.

## How It Works

Starting July 7, 2026, meetings run every other Tuesday at 22:00 KST. On meeting days, the bot runs two scheduled tasks:

1. **9:00 AM KST** — Posts an attendance check message mentioning the `@회고` role. Members react with :white_check_mark: (attending) or :x: (not attending). Selecting one automatically removes the other.
2. **15 min before meeting** — Sends a reminder that mentions only the members who confirmed, nudging them to join the voice channel.

The next meeting can be skipped via a slash command. Attendance data is stored in Redis for 7 days, while skip records are kept for 30 days so they remain valid across the biweekly cadence.

## Quick Start

```bash
# 1. Install dependencies
poetry install

# 2. Configure environment variables (see below)
cp .env.example .env

# 3. Run
poetry run python main.py
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | Yes | Discord bot token |
| `ATTENDANCE_CHANNEL_ID` | Yes | Channel to post attendance messages |
| `RETROSPECTIVE_ROLE_ID` | Yes | Role to mention in attendance checks |
| `VOICE_CHANNEL_ID` | Yes | Voice channel linked in messages |
| `REDIS_URL` | Yes | Redis connection URL |
| `TEST_CHANNEL_ID` | No | Channel for test commands |
| `TEST_ROLE_ID` | No | Role for test commands |

## Slash Commands

| Command | Description |
|---|---|
| `/ping` | Check bot latency |
| `/schedule` | View the next meeting date and time |
| `/skip` | Cancel the next meeting |
| `/sync` | Manually sync slash commands to Discord |
| `/test_morning_check` | Send a test attendance message |
| `/test_evening_reminder` | Send a test reminder based on today's data |

The `/skip` command requires the `@회고` role.

## Architecture

```
bot/ (Discord interface)        ← commands, events, scheduled tasks
  ↓
attendance/                     ← attendance domain (service + repository)
schedule/                       ← schedule domain (service + repository)
  ↓
database/redis.py               ← Redis client
```

The codebase follows a domain-driven layout. Each layer only depends on the one below it. The repository layer is purely functional — async functions over frozen dataclasses, no ORM or class abstractions.

## Deployment

Hosted on [Render](https://render.com) as a Web Service. The bot runs an aiohttp health check server alongside Discord to satisfy Render's port-binding requirement. A [GitHub Actions workflow](.github/workflows/keep-alive.yml) pings the `/health` endpoint periodically to prevent the free-tier service from sleeping.

### Redis Setup

- **Local development**: Use the external Redis URL and allow all IPs (`0.0.0.0/0`) in Render's ingress rules
- **Production**: Use the internal Redis URL (no IP restriction needed)

## Manual Testing

For ad-hoc testing outside of Discord slash commands:

```bash
# Send morning attendance check
poetry run python scripts/send_notification.py morning

# Send evening reminder
poetry run python scripts/send_notification.py evening
```

## Tech Stack

- **Python 3.13+** with **Poetry**
- **discord.py** — slash commands, scheduled tasks, reaction handling
- **Redis** — attendance and schedule data with TTL-based expiration
- **Render** — hosting (web service + key-value store)
