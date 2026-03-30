"""Tests for attack/format compatibility matrix."""

from maldoc.coverage import assess_attack_format


def test_supported_pair_returns_allowed_without_warning():
    allowed, degraded, message = assess_attack_format("metadata", "docx")
    assert allowed is True
    assert degraded is False
    assert message == ""


def test_degraded_pair_returns_warning():
    allowed, degraded, message = assess_attack_format("metadata", "md")
    assert allowed is True
    assert degraded is True
    assert "degraded simulation" in message


def test_unsupported_pair_is_rejected():
    allowed, degraded, message = assess_attack_format("visual_scaling_injection", "odt")
    assert allowed is False
    assert degraded is False
    assert "not supported" in message


def test_rejected_pair_when_not_listed_anywhere():
    allowed, degraded, message = assess_attack_format("off_page", "eml")
    assert allowed is False
    assert degraded is False
    assert "not supported" in message
