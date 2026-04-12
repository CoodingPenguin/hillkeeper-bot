"""Discord utility helpers."""
import discord


async def get_users_who_reacted(
    message: discord.Message,
    emoji: str,
    *,
    exclude_bots: bool = True,
    filter_role: discord.Role | None = None
) -> set[discord.Member]:
    """
    Return the set of members who reacted with the given emoji.

    Iterates through message reactions and collects members matching
    the specified emoji, with optional bot exclusion and role filtering.

    Args:
        message: The message to inspect.
        emoji: Target emoji string (e.g. "✅").
        exclude_bots: Whether to skip bot users.
        filter_role: If set, only include members with this role.

    Returns:
        A set of matching Member objects.
    """
    reacted_users = set()

    for reaction in message.reactions:
        if str(reaction.emoji) == emoji:
            async for user in reaction.users():
                if exclude_bots and user.bot:
                    continue

                member = message.guild.get_member(user.id)
                if not member:
                    continue

                if filter_role and filter_role not in member.roles:
                    continue

                reacted_users.add(member)

    return reacted_users
