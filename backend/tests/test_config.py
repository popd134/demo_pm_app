"""Tests for configuration parsing."""

from __future__ import annotations

from app.core.config import Settings


def test_cors_origins_parsed_from_csv() -> None:
    settings = Settings(cors_origins="http://a.test, http://b.test")
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_accepts_list() -> None:
    settings = Settings(cors_origins=["http://a.test"])
    assert settings.cors_origins == ["http://a.test"]
