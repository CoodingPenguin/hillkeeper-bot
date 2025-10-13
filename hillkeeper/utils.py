"""유틸리티 함수"""
import discord


async def get_users_who_reacted(
    message: discord.Message,
    emoji: str,
    *,
    exclude_bots: bool = True,
    filter_role: discord.Role | None = None
) -> set[discord.Member]:
    """
    특정 이모지로 반응한 사용자 목록을 반환합니다.
    메시지의 반응을 순회하며 지정된 이모지에 반응한 멤버들을 수집합니다.
    봇 제외 및 역할 필터링 옵션을 제공합니다.

    Args:
        message: 확인할 메시지
        emoji: 확인할 이모지 (예: "✅")
        exclude_bots: 봇을 제외할지 여부 (기본값: True)
        filter_role: 특정 역할을 가진 사용자만 필터링 (기본값: None)

    Returns:
        반응한 사용자 집합 (Member 객체)
    """
    reacted_users = set()

    for reaction in message.reactions:
        if str(reaction.emoji) == emoji:
            async for user in reaction.users():
                # 봇 제외 옵션
                if exclude_bots and user.bot:
                    continue

                # Member 객체로 변환
                member = message.guild.get_member(user.id)
                if not member:
                    continue

                # 역할 필터링
                if filter_role and filter_role not in member.roles:
                    continue

                reacted_users.add(member)

    return reacted_users
