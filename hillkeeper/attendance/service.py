"""Attendance business logic."""
import logging

import discord

from ..config import (
    DEFAULT_MEETING_HOUR,
    DEFAULT_MEETING_MINUTE,
    EMOJI_CHECK,
    EMOJI_CROSS,
    get_env,
)
from ..messages import create_morning_check_embed, create_evening_reminder_embed, create_no_participants_embed
from ..utils import get_users_who_reacted
from . import repository

logger = logging.getLogger('hillkeeper')


def _get_channel(bot, channel_id: str) -> discord.TextChannel | None:
    """
    Look up a channel by ID, logging an error if not found.

    Args:
        bot: The Discord bot instance.
        channel_id: Channel ID string.
    """
    channel = bot.get_channel(int(channel_id))
    if not channel:
        logger.error(f"Channel not found: {channel_id}")
    return channel


async def _get_participated_members(
    channel, message_id: int, role: discord.Role
) -> set[discord.Member]:
    """
    Collect members who reacted with the check emoji.

    Args:
        channel: The Discord channel.
        message_id: Attendance check message ID.
        role: Role to filter by.

    Returns:
        A set of participating members.

    Raises:
        ValueError: If the message could not be fetched.
    """
    try:
        message = await channel.fetch_message(message_id)
        return await get_users_who_reacted(
            message,
            EMOJI_CHECK,
            exclude_bots=True,
            filter_role=role
        )
    except Exception as e:
        logger.error(f"Failed to fetch message {message_id}: {e}")
        await repository.delete_event(message_id)
        raise ValueError(f"Failed to fetch attendance message: {message_id}") from e


async def _send_reminder_or_empty(
    channel, members: set, voice_channel_id: str, *,
    meeting_hour: int,
    meeting_minute: int,
):
    """
    Send either a participant reminder or a "no one showed up" message.

    Args:
        channel: The Discord channel.
        members: Set of participating members.
        voice_channel_id: Voice channel ID string.
        meeting_hour: Meeting hour to display.
        meeting_minute: Meeting minute to display.
    """
    if members and len(members) > 1:
        mentions = " ".join([member.mention for member in members])
        content, embed = create_evening_reminder_embed(
            mentions,
            int(voice_channel_id),
            meeting_hour=meeting_hour,
            meeting_minute=meeting_minute,
        )
        await channel.send(content=content, embed=embed)
        logger.info(f"Evening reminder sent to {len(members)} members")
    else:
        embed = create_no_participants_embed()
        await channel.send(embed=embed)
        logger.info(f"Not enough participants: {len(members) if members else 0} members")


async def send_morning_check(
    bot, channel_id: str, role_id: str, *,
    is_test: bool = False,
    meeting_hour: int = DEFAULT_MEETING_HOUR,
    meeting_minute: int = DEFAULT_MEETING_MINUTE,
):
    """
    Send the morning attendance check message.

    Posts an embed with check/cross reactions and persists the
    event to Redis. Uses a 1-minute TTL in test mode, 7-day TTL
    in production.

    Args:
        bot: The Discord bot instance.
        channel_id: Target channel ID.
        role_id: Role ID to mention.
        is_test: Whether this is a test invocation.
        meeting_hour: Meeting hour to display.
        meeting_minute: Meeting minute to display.
    """
    try:
        channel = _get_channel(bot, channel_id)
        if not channel:
            return

        voice_channel_id = get_env('VOICE_CHANNEL_ID', required=True)
        content, embed = create_morning_check_embed(
            int(role_id),
            int(voice_channel_id),
            meeting_hour=meeting_hour,
            meeting_minute=meeting_minute,
        )
        message = await channel.send(content=content, embed=embed)

        await message.add_reaction(EMOJI_CHECK)
        await message.add_reaction(EMOJI_CROSS)

        ttl = 60 if is_test else repository.TTL_7_DAYS
        await repository.save_event(
            message.id,
            channel_id=channel.id,
            role_id=int(role_id),
            ttl=ttl
        )

        logger.info(f"Morning check message sent: {message.id} (test={is_test}, ttl={ttl}s)")

    except Exception as e:
        logger.error(f"Failed to send morning check message: {e}")
        raise


async def send_evening_reminder(
    bot, channel_id: str, role_id: str, *,
    meeting_hour: int = DEFAULT_MEETING_HOUR,
    meeting_minute: int = DEFAULT_MEETING_MINUTE,
):
    """
    Send the evening reminder to confirmed participants.

    Fetches today's latest attendance message, collects members
    who reacted with the check emoji, and sends an appropriate
    reminder or a "no participants" notice.

    Args:
        bot: The Discord bot instance.
        channel_id: Target channel ID.
        role_id: Role ID to filter by.
        meeting_hour: Meeting hour to display.
        meeting_minute: Meeting minute to display.
    """
    try:
        channel = _get_channel(bot, channel_id)
        if not channel:
            return

        role = channel.guild.get_role(int(role_id))
        if not role:
            logger.error(f"Role not found: {role_id}")
            return

        message_ids = await repository.get_today_messages()
        if not message_ids:
            raise ValueError("No attendance messages found for today")

        latest_message_id = max(message_ids)
        logger.info(f"Using latest attendance message: {latest_message_id}")

        members = await _get_participated_members(channel, latest_message_id, role)

        voice_channel_id = get_env('VOICE_CHANNEL_ID', required=True)
        await _send_reminder_or_empty(
            channel,
            members,
            voice_channel_id,
            meeting_hour=meeting_hour,
            meeting_minute=meeting_minute,
        )

    except Exception as e:
        logger.error(f"Failed to send evening reminder: {e}")
        raise
