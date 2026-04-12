"""messages.py 테스트"""
from hillkeeper.config import EMOJI_CHECK, EMOJI_CROSS
from hillkeeper.messages import (
    create_morning_check_embed,
    create_evening_reminder_embed,
    create_no_participants_embed,
)


class TestCreateMorningCheckEmbed:

    def test_content_mentions_role(self):
        content, _ = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert "<@&200>" in content

    def test_embed_title(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert "출석" in embed.title or "참석" in embed.title

    def test_embed_description_contains_emojis(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert EMOJI_CHECK in embed.description
        assert EMOJI_CROSS in embed.description

    def test_embed_has_two_fields(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert len(embed.fields) == 2

    def test_embed_voice_channel_field(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        channel_field = embed.fields[1]
        assert "<#300>" in channel_field.value

    def test_embed_footer(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert embed.footer.text is not None

    def test_embed_color(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert embed.color.value == 0x58ABFF


class TestCreateEveningReminderEmbed:

    def test_content_is_mentions(self):
        mentions = "<@1001> <@1002>"
        content, _ = create_evening_reminder_embed(mentions, voice_channel_id=300)
        assert content == mentions

    def test_embed_description_contains_channel(self):
        _, embed = create_evening_reminder_embed("<@1001>", voice_channel_id=300)
        assert "<#300>" in embed.description

    def test_embed_color(self):
        _, embed = create_evening_reminder_embed("<@1001>", voice_channel_id=300)
        assert embed.color.value == 0xF1C40F


class TestCreateNoParticipantsEmbed:

    def test_embed_has_title(self):
        embed = create_no_participants_embed()
        assert embed.title is not None

    def test_embed_color(self):
        embed = create_no_participants_embed()
        assert embed.color.value == 0x34A5DB
