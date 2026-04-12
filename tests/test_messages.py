"""Tests for messages.py."""
from hillkeeper.config import EMOJI_CHECK, EMOJI_CROSS, COLOR_GREEN
from hillkeeper.messages import (
    create_morning_check_embed,
    create_evening_reminder_embed,
    create_no_participants_embed,
    create_schedule_changed_embed,
    create_schedule_skipped_embed,
    create_default_changed_embed,
    create_schedule_view_embed,
)


class TestCreateMorningCheckEmbed:

    def test_content_mentions_role(self):
        content, _ = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert "<@&200>" in content

    def test_embed_title(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert embed.title == "📋️회고 모임 참석 여부 확인"

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
        assert embed.footer.text == "⚠️ 참석과 불참을 모두 누르면 마지막 선택만 남아요."

    def test_embed_color(self):
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert embed.color.value == 0x58ABFF

    def test_dynamic_meeting_time(self):
        """Meeting time should be reflected in the embed."""
        _, embed = create_morning_check_embed(
            role_id=200, voice_channel_id=300, meeting_hour=21, meeting_minute=0
        )
        assert "21:00" in embed.fields[0].value

    def test_default_meeting_time(self):
        """Default meeting time should be 22:00."""
        _, embed = create_morning_check_embed(role_id=200, voice_channel_id=300)
        assert "22:00" in embed.fields[0].value


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

    def test_dynamic_meeting_time(self):
        """Meeting time should be reflected in the description."""
        _, embed = create_evening_reminder_embed(
            "<@1001>", voice_channel_id=300, meeting_hour=21, meeting_minute=0
        )
        assert "21:00" in embed.description


class TestCreateNoParticipantsEmbed:

    def test_embed_has_title(self):
        embed = create_no_participants_embed()
        assert embed.title == "🐮 언덕지기가 혼자 언덕을 지키고 있어요!"

    def test_description_contains_story_prompt(self):
        embed = create_no_participants_embed()
        assert "언덕지기에게 이번 주 이야기를 조금 들려주세요!" in embed.description

    def test_embed_color(self):
        embed = create_no_participants_embed()
        assert embed.color.value == 0x34A5DB


class TestCreateScheduleChangedEmbed:

    def test_contains_day_and_time(self):
        content, embed = create_schedule_changed_embed(
            day_name="금요일", hour=22, minute=0
        )
        assert "금요일" in embed.description
        assert "22:00" in embed.description

    def test_embed_color_is_green(self):
        _, embed = create_schedule_changed_embed(
            day_name="금요일", hour=22, minute=0
        )
        assert embed.color.value == COLOR_GREEN


class TestCreateScheduleSkippedEmbed:

    def test_contains_cancel_message(self):
        content, embed = create_schedule_skipped_embed(day_name="목요일")
        assert "취소" in embed.description
        assert "목요일" in embed.description


class TestCreateDefaultChangedEmbed:

    def test_contains_new_default(self):
        content, embed = create_default_changed_embed(
            day_name="수요일", hour=21, minute=0
        )
        assert "수요일" in embed.description
        assert "21:00" in embed.description


class TestCreateScheduleViewEmbed:

    def test_shows_default_schedule(self):
        embed = create_schedule_view_embed(
            day_name="목요일", hour=22, minute=0
        )
        assert "목요일" in embed.description
        assert "22:00" in embed.description

    def test_shows_override_info(self):
        embed = create_schedule_view_embed(
            day_name="목요일", hour=22, minute=0,
            override_text="이번 주: 금요일 22:00로 변경됨"
        )
        assert "금요일" in embed.description or "금요일" in str(embed.fields)
