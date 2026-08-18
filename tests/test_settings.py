"""Tests for configuration loading, clamping and defaults."""

from pathlib import Path

import pytest

from pacman.settings import MIN_LEVELS, ConfigError, load_config


def write(tmp_path: Path, text: str) -> Path:
    """Write *text* into a temporary configuration file."""
    path = tmp_path / "config.json"
    path.write_text(text, encoding="utf-8")
    return path


def test_defaults_are_used_when_keys_are_missing(tmp_path: Path) -> None:
    """An empty object still yields a playable configuration."""
    config, warnings = load_config(write(tmp_path, "{}"))
    assert config.lives == 3
    assert config.level_count >= MIN_LEVELS
    assert any("lives" in message for message in warnings)


def test_out_of_range_values_are_clamped(tmp_path: Path) -> None:
    """A silly value is clamped and reported."""
    config, warnings = load_config(write(tmp_path, '{"lives": 9999}'))
    assert config.lives == 99
    assert any("out of range" in message for message in warnings)


def test_wrong_types_fall_back(tmp_path: Path) -> None:
    """A string where a number is expected does not crash."""
    config, warnings = load_config(write(tmp_path, '{"lives": "three"}'))
    assert config.lives == 3
    assert any("must be a number" in message for message in warnings)


def test_unknown_keys_are_ignored(tmp_path: Path) -> None:
    """Unknown keys are reported but never fatal."""
    _, warnings = load_config(write(tmp_path, '{"wat": 1}'))
    assert any("unknown key" in message for message in warnings)


def test_level_list_is_padded(tmp_path: Path) -> None:
    """The game always holds at least ten levels."""
    text = '{"levels": [{"width": 15, "height": 11}]}'
    config, _ = load_config(write(tmp_path, text))
    assert config.level_count == MIN_LEVELS


def test_broken_level_entries_are_dropped(tmp_path: Path) -> None:
    """A malformed level entry is skipped, the rest still loads."""
    text = '{"levels": [42, {"width": 17, "height": 13}]}'
    config, warnings = load_config(write(tmp_path, text))
    assert config.levels[0].width == 17
    assert any("must be an object" in message for message in warnings)


def test_highscore_path_follows_the_config(tmp_path: Path) -> None:
    """A relative highscore file sits next to the configuration."""
    text = '{"highscore_filename": "scores.json"}'
    config, _ = load_config(write(tmp_path, text))
    assert config.highscore_path.parent == tmp_path.resolve()


def test_missing_file_is_reported(tmp_path: Path) -> None:
    """A missing file raises a readable error, never a traceback."""
    with pytest.raises(ConfigError) as error:
        load_config(tmp_path / "nope.json")
    assert "not found" in str(error.value)


def test_non_object_document_is_reported(tmp_path: Path) -> None:
    """A JSON array is not a configuration."""
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, "[1, 2, 3]"))
