"""Cheat switches, meant to make the peer review painless.

The subject asks for a cheat mode that genuinely helps a reviewer
reach every feature of the game, so the switches below cover the
awkward parts: surviving the ghosts, skipping ahead to a later level,
freezing the board to inspect it and clearing a level instantly.
"""

from dataclasses import dataclass
from typing import Final

SPEED_MULTIPLIER: Final = 1.7


@dataclass
class Cheats:
    """The state of every cheat switch."""

    enabled: bool = False
    invincible: bool = False
    frozen_ghosts: bool = False
    fast_player: bool = False
    show_targets: bool = False

    def toggle_enabled(self) -> None:
        """Turn the whole cheat mode on or off."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.invincible = False
            self.frozen_ghosts = False
            self.fast_player = False
            self.show_targets = False

    @property
    def player_speed_factor(self) -> float:
        """Return the multiplier applied to the player speed."""
        if self.enabled and self.fast_player:
            return SPEED_MULTIPLIER
        return 1.0

    @property
    def is_invincible(self) -> bool:
        """Return ``True`` when ghosts cannot hurt the player."""
        return self.enabled and self.invincible

    @property
    def ghosts_are_frozen(self) -> bool:
        """Return ``True`` when ghosts must stand still."""
        return self.enabled and self.frozen_ghosts

    @property
    def targets_visible(self) -> bool:
        """Return ``True`` when ghost targets are drawn on screen."""
        return self.enabled and self.show_targets

    def summary(self) -> list[tuple[str, str, bool]]:
        """Return the (key, label, active) triples shown on screen."""
        return [
            ("F2", "INVINCIBLE", self.invincible),
            ("F3", "FREEZE GHOSTS", self.frozen_ghosts),
            ("F4", "TURBO PACMAN", self.fast_player),
            ("F5", "SHOW TARGETS", self.show_targets),
            ("F6", "SKIP LEVEL", False),
            ("F7", "EXTRA LIFE", False),
            ("F8", "EAT ALL BUT ONE", False),
        ]
