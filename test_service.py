import service
import pytest


def test_is_tachycardic(capsys):
    assert service.is_tachycardic(135, 6) is True
    assert service.is_tachycardic(110, 50) is True
    assert service.is_tachycardic(160, 0.2) is False
    assert service.is_tachycardic(140, 8) is True
