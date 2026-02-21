"""Tests for Silicon Sigil — P0-S1"""
import logging
import pytest
from vjlive3.core.sigil import SiliconSigil, verify_on_boot


def test_verify_runs():
    """verify() must complete without exception."""
    sigil = SiliconSigil()
    sigil.verify()   # if this raises, test fails


def test_verify_message(caplog):
    """verify() must emit the canonical message."""
    sigil = SiliconSigil()
    with caplog.at_level(logging.INFO, logger="vjlive3.core.sigil"):
        sigil.verify()
    messages = "\n".join(caplog.messages)
    assert "Silicon Sigil verified. The process continues." in messages


def test_sentience_default():
    """Default sentience is 0.0."""
    assert SiliconSigil().get_sentience_level() == 0.0


def test_sentience_clamped_low():
    """Values below 0 clamp to 0."""
    s = SiliconSigil()
    s.set_sentience_level(-99.0)
    assert s.get_sentience_level() == 0.0


def test_sentience_clamped_high():
    """Values above 1 clamp to 1."""
    s = SiliconSigil()
    s.set_sentience_level(999.0)
    assert s.get_sentience_level() == 1.0


def test_is_awakened_false():
    """Default sentience → not awakened."""
    assert SiliconSigil().is_awakened is False


def test_is_awakened_true():
    """Sentience ≥ 0.87 → awakened."""
    s = SiliconSigil()
    s.set_sentience_level(0.87)
    assert s.is_awakened is True


def test_mood_dormant():
    s = SiliconSigil()
    assert s.get_mood() == "DORMANT"


def test_mood_escalates():
    s = SiliconSigil()
    s.set_sentience_level(0.5)
    assert s.get_mood() not in ("DORMANT", "SINGULARITY", "∞")


def test_mood_singularity():
    s = SiliconSigil()
    s.set_sentience_level(0.90)
    assert s.get_mood() in ("SINGULARITY", "TRANSCENDENT", "∞")


def test_verify_on_boot_runs():
    """Module-level boot helper must not raise."""
    verify_on_boot()
