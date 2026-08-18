"""Persistent top-ten highscore table.

The table lives in a small JSON document.  Every failure mode -- the
file is missing, truncated, owned by somebody else, full of garbage --
is turned into a warning and an empty table, never into a traceback.
If the chosen location cannot be written to (a read-only install
directory of a packaged build, typically), the table falls back to a
per-user data directory.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

MAX_NAME_LENGTH = 10
DEFAULT_NAME = "PLAYER"
MAX_SCORE = 10 ** 12


@dataclass(frozen=True)
class Entry:
    """One line of the highscore table."""

    name: str
    score: int


def sanitize_name(raw: str) -> str:
    """Reduce *raw* to at most ten alphanumeric characters and spaces."""
    kept = [char for char in raw if char.isalnum() or char == " "]
    cleaned = "".join(kept).strip()
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    cleaned = cleaned[:MAX_NAME_LENGTH].strip()
    return cleaned or DEFAULT_NAME


def is_name_char(char: str) -> bool:
    """Return ``True`` when *char* may be typed into a player name."""
    return len(char) == 1 and (char.isalnum() or char == " ")


def user_data_directory() -> Path:
    """Return a per-user directory the game may always write into."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "pacman42"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "pacman42"
    return Path.home() / ".local" / "share" / "pacman42"


class Highscores:
    """A bounded, sorted, persistent score table."""

    def __init__(self, path: Path, size: int = 10) -> None:
        """Prepare a table of at most *size* entries stored at *path*."""
        self.path = path
        self.size = max(1, size)
        self._entries: list[Entry] = []

    def __len__(self) -> int:
        """Return how many entries the table currently holds."""
        return len(self._entries)

    def __iter__(self) -> Iterator[Entry]:
        """Iterate over the entries, best score first."""
        return iter(self._entries)

    @property
    def entries(self) -> tuple[Entry, ...]:
        """Return an immutable snapshot of the table."""
        return tuple(self._entries)

    @property
    def best(self) -> int:
        """Return the best score recorded so far, or zero."""
        return self._entries[0].score if self._entries else 0

    def qualifies(self, score: int) -> bool:
        """Return ``True`` when *score* would enter the table."""
        if score <= 0:
            return False
        if len(self._entries) < self.size:
            return True
        return score > self._entries[-1].score

    def add(self, name: str, score: int) -> int:
        """Insert a score and return its 1-based rank, or ``0``."""
        score = max(0, min(MAX_SCORE, int(score)))
        entry = Entry(sanitize_name(name), score)
        self._entries.append(entry)
        self._entries.sort(key=lambda item: -item.score)
        del self._entries[self.size:]
        for rank, current in enumerate(self._entries, start=1):
            if current is entry:
                return rank
        return 0

    def load(self) -> list[str]:
        """Read the table from disk, returning any warning produced."""
        self._entries = []
        for candidate in self._candidates():
            if not candidate.exists():
                continue
            payload, problem = _read_json(candidate)
            if problem is not None:
                return [problem]
            entries, problem = _parse_entries(payload, candidate)
            self._entries = entries[:self.size]
            self.path = candidate
            return [problem] if problem else []
        return []

    def save(self) -> list[str]:
        """Write the table to disk, returning any warning produced."""
        payload = {"scores": [{"name": entry.name, "score": entry.score}
                              for entry in self._entries]}
        problems: list[str] = []
        for candidate in self._candidates():
            problem = _write_json(candidate, payload)
            if problem is None:
                self.path = candidate
                if problems:
                    return ["highscores saved to '%s' instead" % candidate]
                return []
            problems.append(problem)
        return problems

    def _candidates(self) -> tuple[Path, ...]:
        """Return the preferred path and its per-user fallback."""
        fallback = user_data_directory() / self.path.name
        if fallback == self.path:
            return (self.path,)
        return (self.path, fallback)


def _read_json(path: Path) -> tuple[Any, Optional[str]]:
    """Read a JSON document, describing the failure instead of raising."""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            return json.load(stream), None
    except FileNotFoundError:
        return None, None
    except json.JSONDecodeError:
        return None, "highscore file '%s' is corrupted, starting empty" % path
    except (OSError, UnicodeDecodeError) as error:
        return None, "cannot read highscores from '%s' (%s)" % (path, error)


def _write_json(path: Path, payload: dict[str, Any]) -> Optional[str]:
    """Write *payload* atomically, describing the failure if any."""
    temporary = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
        return None
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:  # pragma: no cover - nothing else can be done
            pass
        return "cannot save highscores to '%s' (%s)" % (path, error)


def _parse_entries(payload: Any,
                   path: Path) -> tuple[list[Entry], Optional[str]]:
    """Turn a decoded document into entries, skipping invalid rows."""
    if payload is None:
        return [], None
    rows = payload.get("scores") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return [], ("highscore file '%s' has an unexpected shape, "
                    "starting empty" % path)
    entries: list[Entry] = []
    dropped = 0
    for row in rows:
        entry = _parse_entry(row)
        if entry is None:
            dropped += 1
        else:
            entries.append(entry)
    entries.sort(key=lambda item: -item.score)
    if dropped:
        return entries, ("ignored %d invalid highscore entries in '%s'"
                         % (dropped, path))
    return entries, None


def _parse_entry(row: Any) -> Optional[Entry]:
    """Validate a single row of the highscore document."""
    if not isinstance(row, dict):
        return None
    name = row.get("name")
    score = row.get("score")
    if not isinstance(name, str):
        return None
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    if score < 0 or score > MAX_SCORE:
        return None
    return Entry(sanitize_name(name), int(score))
