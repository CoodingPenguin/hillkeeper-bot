"""Discord event handlers."""
import logging

from ..config import EMOJI_CHECK, EMOJI_CROSS
from ..attendance import repository

logger = logging.getLogger('hillkeeper')


async def handle_attendance_reaction(bot, payload):
    """
    Process an emoji reaction on an attendance check message.

    Enforces exclusive selection by removing the opposite emoji
    and persists the user's response to Redis.

    Args:
        bot: The Discord bot instance.
        payload: The raw reaction event payload.
    """
    if payload.user_id == bot.user.id:
        return

    if str(payload.emoji) not in [EMOJI_CHECK, EMOJI_CROSS]:
        return

    # Only handle reactions on tracked attendance messages
    event = await repository.get_event(payload.message_id)
    if not event:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    try:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
    except Exception as e:
        logger.error(f"Failed to fetch message {payload.message_id}: {e}")
        return

    # Remove the opposite emoji to enforce single selection
    opposite_emoji = EMOJI_CROSS if str(payload.emoji) == EMOJI_CHECK else EMOJI_CHECK
    try:
        await message.remove_reaction(opposite_emoji, member)
    except Exception as e:
        logger.debug(f"Failed to remove opposite reaction: {e}")

    response = "yes" if str(payload.emoji) == EMOJI_CHECK else "no"
    await repository.save_response(
        payload.message_id,
        payload.user_id,
        username=member.display_name,
        response=response
    )

    logger.info(f"User {member.display_name} ({payload.user_id}) reacted with {payload.emoji}")


def register_events(bot):
    """Register event handlers on the bot."""

    @bot.event
    async def on_ready():
        logger.info(f'Bot is ready: {bot.user}')
        logger.info(f'Bot ID: {bot.user.id}')
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    @bot.event
    async def on_raw_reaction_add(payload):
        await handle_attendance_reaction(bot, payload)
