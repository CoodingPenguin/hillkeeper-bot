"""config.py 테스트"""
import pytest

from hillkeeper.config import get_env


class TestGetEnv:

    def test_returns_value(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "hello")
        assert get_env("TEST_KEY") == "hello"

    def test_returns_default_when_missing(self, monkeypatch):
        monkeypatch.delenv("TEST_KEY", raising=False)
        assert get_env("TEST_KEY", default="fallback") == "fallback"

    def test_returns_none_when_no_default(self, monkeypatch):
        monkeypatch.delenv("TEST_KEY", raising=False)
        assert get_env("TEST_KEY") is None

    def test_required_raises_when_missing(self, monkeypatch):
        monkeypatch.delenv("TEST_KEY", raising=False)
        with pytest.raises(ValueError, match="TEST_KEY"):
            get_env("TEST_KEY", required=True)

    def test_required_returns_value_when_present(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "value")
        assert get_env("TEST_KEY", required=True) == "value"
