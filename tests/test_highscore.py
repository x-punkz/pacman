"""Tests for the persistent highscore table."""

from pathlib import Path

from pacman.highscore import Highscores, sanitize_name


def test_names_are_reduced_to_ten_safe_characters() -> None:
    """Only letters, digits and single spaces survive."""
    assert sanitize_name("  Da/ni!!  Viei  ") == "Dani Viei"
    assert sanitize_name("###") == "PLAYER"
    assert len(sanitize_name("abcdefghijklmnop")) == 10


def test_table_keeps_the_best_ten(tmp_path: Path) -> None:
    """Only the ten best scores are stored, sorted."""
    table = Highscores(tmp_path / "scores.json", size=10)
    for value in range(20):
        table.add("P%d" % value, value * 10)
    assert len(table) == 10
    assert table.best == 190
    assert [entry.score for entry in table] == sorted(
        [entry.score for entry in table], reverse=True)


def test_round_trip(tmp_path: Path) -> None:
    """A saved table reads back identical."""
    path = tmp_path / "scores.json"
    table = Highscores(path)
    table.add("DANIVIEI", 4200)
    assert table.save() == []
    reloaded = Highscores(path)
    assert reloaded.load() == []
    assert reloaded.entries[0].name == "DANIVIEI"
    assert reloaded.entries[0].score == 4200


def test_corrupted_file_starts_empty(tmp_path: Path) -> None:
    """Garbage on disk produces a warning, not a crash."""
    path = tmp_path / "scores.json"
    path.write_text("{not json at all", encoding="utf-8")
    table = Highscores(path)
    warnings = table.load()
    assert len(table) == 0
    assert warnings and "corrupted" in warnings[0]


def test_invalid_rows_are_skipped(tmp_path: Path) -> None:
    """Bad entries are dropped, good ones survive."""
    path = tmp_path / "scores.json"
    path.write_text(
        '{"scores": [{"name": "OK", "score": 10}, {"name": 5},'
        ' {"score": -3, "name": "NEG"}, "junk"]}', encoding="utf-8")
    table = Highscores(path)
    warnings = table.load()
    assert [entry.name for entry in table] == ["OK"]
    assert warnings and "invalid" in warnings[0]


def test_missing_file_is_not_an_error(tmp_path: Path) -> None:
    """A first run starts with an empty table."""
    table = Highscores(tmp_path / "absent.json")
    assert table.load() == []
    assert len(table) == 0


def test_qualification_rules(tmp_path: Path) -> None:
    """A score enters the table only when it deserves to."""
    table = Highscores(tmp_path / "scores.json", size=2)
    assert not table.qualifies(0)
    assert table.qualifies(10)
    table.add("A", 100)
    table.add("B", 50)
    assert table.qualifies(60)
    assert not table.qualifies(20)


def test_scores_are_stored_as_positive_integers(tmp_path: Path) -> None:
    """A negative score is clamped to zero."""
    table = Highscores(tmp_path / "scores.json")
    table.add("X", -5)
    assert table.entries[0].score == 0
