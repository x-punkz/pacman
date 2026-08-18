"""Full screen views: menus, HUD and overlays."""

import math
from typing import Sequence

from ..game import direction as compass
from ..game.cheats import Cheats
from ..settings import Config
from ..game.ghosts import GhostKind
from ..game.session import Session
from ..highscore import Highscores, MAX_NAME_LENGTH
from . import sprites, theme
from .render import Renderer

MENU_ITEMS: tuple[str, ...] = (
    "START GAME", "VIEW HIGHSCORES", "INSTRUCTIONS", "EXIT")

PAUSE_ITEMS: tuple[str, ...] = ("RESUME GAME", "RETURN TO MAIN MENU")

CONTROLS: tuple[tuple[str, str], ...] = (
    ("ARROW KEYS / WASD", "move Pac-Man"),
    ("P or ESC", "pause the game"),
    ("ENTER", "validate a menu entry"),
    ("UP / DOWN", "move through a menu"),
    ("F1", "turn the cheat mode on or off"),
)

RULES: tuple[str, ...] = (
    "EAT EVERY PACGUM TO CLEAR THE LEVEL",
    "SUPER-PACGUMS SIT IN THE FOUR CORNERS",
    "THEY MAKE THE GHOSTS EDIBLE FOR A FEW SECONDS",
    "A GHOST THAT TOUCHES YOU COSTS ONE LIFE",
    "THE LEVEL CLOCK COSTS A LIFE WHEN IT RUNS OUT",
)


def draw_menu(renderer: Renderer, selection: int, scores: Highscores,
              notice: str, clock: float) -> None:
    """Draw the main menu."""
    renderer.clear()
    _draw_title(renderer, clock)
    top = int(renderer.height * 0.44)
    for index, label in enumerate(MENU_ITEMS):
        selected = index == selection
        color = theme.ACCENT if selected else theme.TEXT_DIM
        row = top + index * int(renderer.height * 0.075)
        renderer.text_center(row, label, color, 3)
        if selected:
            width = renderer.mlx.text_width(label, 3)
            left = (renderer.width - width) // 2
            sprites.draw_pacman(renderer.frame, left - 26,
                                row + renderer.mlx.text_height(3) // 2, 10,
                                compass.RIGHT, 0.4 + 0.4 * abs(
                                    math.sin(clock * 5.0)))
    _draw_menu_scores(renderer, scores)
    if notice:
        renderer.text_center(int(renderer.height * 0.90), notice,
                             theme.DANGER, 1)
    _draw_footer(renderer, "UP / DOWN TO CHOOSE     ENTER TO VALIDATE")


def _draw_menu_scores(renderer: Renderer, scores: Highscores) -> None:
    """Show the three best scores straight on the main menu."""
    top = int(renderer.height * 0.755)
    renderer.text_center(top, "HIGHSCORES", theme.TEXT_DIM, 1)
    entries = scores.entries[:3]
    if not entries:
        renderer.text_center(top + 22, "NO SCORE YET - BE THE FIRST",
                             theme.TEXT_DIM, 2)
        return
    left = int(renderer.width * 0.34)
    right = int(renderer.width * 0.66)
    for index, entry in enumerate(entries):
        row = top + 22 + index * 26
        color = theme.ACCENT if index == 0 else theme.TEXT
        renderer.text(left, row, "%d" % (index + 1), theme.TEXT_DIM, 2)
        renderer.text(left + 28, row, entry.name.upper(), color, 2)
        renderer.text_right(right, row, str(entry.score), color, 2)


def _draw_title(renderer: Renderer, clock: float) -> None:
    """Draw the logo and the little chase under it."""
    renderer.text_center(int(renderer.height * 0.10), "PAC-MAN",
                         theme.ACCENT, 7)
    renderer.text_center(int(renderer.height * 0.20),
                         "GHOSTS! MORE GHOSTS!", theme.TEXT, 2)
    row = int(renderer.height * 0.30)
    span = min(renderer.width - 120, 460)
    start = (renderer.width - span) // 2
    offset = int((clock * 60.0) % (span + 120)) - 60
    sprites.draw_pacman(renderer.frame, start + offset, row, 14,
                        compass.RIGHT, 0.35 + 0.35 * abs(
                            math.sin(clock * 6.0)))
    kinds = (GhostKind.BLINKY, GhostKind.PINKY, GhostKind.INKY,
             GhostKind.CLYDE)
    for index, kind in enumerate(kinds):
        sprites.draw_ghost(renderer.frame, start + offset - 46 - index * 40,
                           row, 26, theme.ghost_color(kind), compass.RIGHT)


def draw_highscores(renderer: Renderer, scores: Highscores,
                    notice: str) -> None:
    """Draw the top ten table."""
    renderer.clear()
    renderer.text_center(int(renderer.height * 0.08), "HIGHSCORES",
                         theme.ACCENT, 5)
    left = int(renderer.width * 0.24)
    right = int(renderer.width * 0.76)
    top = int(renderer.height * 0.24)
    step = int(renderer.height * 0.055)
    entries = scores.entries
    for index in range(scores.size):
        row = top + index * step
        if index < len(entries):
            entry = entries[index]
            color = theme.ACCENT if index == 0 else theme.TEXT
            name, value = entry.name.upper(), str(entry.score)
        else:
            color = theme.TEXT_DIM
            name, value = "- - - - -", "0"
        renderer.text(left, row, "%2d" % (index + 1), theme.TEXT_DIM, 2)
        renderer.text(left + 52, row, name, color, 2)
        renderer.text_right(right, row, value, color, 2)
    if not entries:
        renderer.text_center(int(renderer.height * 0.86),
                             "NO SCORE YET - BE THE FIRST", theme.TEXT_DIM, 1)
    else:
        renderer.text_center(int(renderer.height * 0.86),
                             "SAVED IN %s" % scores.path.name.upper(),
                             theme.TEXT_DIM, 1)
    if notice:
        renderer.text_center(int(renderer.height * 0.90), notice,
                             theme.DANGER, 1)
    _draw_footer(renderer, "ESC OR ENTER TO GO BACK")


def draw_instructions(renderer: Renderer, config: Config) -> None:
    """Draw the controls, the rules, the cheats and the scoring."""
    renderer.clear()
    renderer.text_center(int(renderer.height * 0.05), "INSTRUCTIONS",
                         theme.ACCENT, 4)
    left = int(renderer.width * 0.05)
    right = int(renderer.width * 0.52)
    start = int(renderer.height * 0.18)
    line = 20
    row = _section(renderer, left, start, "CONTROLS")
    for key, action in CONTROLS:
        renderer.text(left, row, key, theme.TEXT, 1)
        renderer.text(left + 200, row, action.upper(), theme.TEXT_DIM, 1)
        row += line
    row = _section(renderer, left, row + line, "RULES")
    for rule in RULES:
        renderer.text(left, row, rule, theme.TEXT_DIM, 1)
        row += line
    row = _section(renderer, right, start, "CHEAT MODE")
    renderer.text(right, row, "PRESS F1 WHILE PLAYING TO UNLOCK",
                  theme.TEXT_DIM, 1)
    row += line + 4
    for key, label, _active in Cheats().summary():
        renderer.text(right, row, key, theme.TEXT, 1)
        renderer.text(right + 44, row, label, theme.TEXT_DIM, 1)
        row += line
    row = _section(renderer, right, row + line, "SCORING")
    for label, value in (("PACGUM", config.points_per_pacgum),
                         ("SUPER-PACGUM", config.points_per_super_pacgum),
                         ("GHOST", config.points_per_ghost)):
        renderer.text(right, row, label, theme.TEXT_DIM, 1)
        renderer.text_right(right + 240, row, "+%d" % value, theme.TEXT, 1)
        row += line
    renderer.text(right, row + 6, "%d LEVELS, %d LIVES, %d SECONDS EACH"
                  % (config.level_count, config.lives,
                     int(config.level_max_time)), theme.TEXT_DIM, 1)
    _draw_footer(renderer, "ESC OR ENTER TO GO BACK")


def _section(renderer: Renderer, x: int, y: int, title: str) -> int:
    """Draw a section heading and return the first content row."""
    renderer.text(x, y, title, theme.SUCCESS, 2)
    renderer.frame.fill_rect(x, y + 20, renderer.mlx.text_width(title, 2),
                             2, theme.WALL)
    return y + 32


def draw_hud(renderer: Renderer, session: Session, best: int) -> None:
    """Draw the permanent in-game header."""
    width = renderer.width
    renderer.frame.fill_rect(0, 0, width, theme.HUD_HEIGHT, theme.PANEL)
    renderer.frame.fill_rect(0, theme.HUD_HEIGHT - 2, width, 2,
                             theme.WALL)
    level = session.level
    columns = (0.02, 0.19, 0.35, 0.50, 0.66)
    values = (
        ("SCORE", "%d" % session.score, theme.ACCENT),
        ("HIGH", "%d" % max(best, session.score), theme.TEXT),
        ("LEVEL", "%d / %d" % (session.level_number, session.level_count),
         theme.TEXT),
        ("PACGUMS", "%d" % level.remaining_pacgums, theme.TEXT),
        ("TIME", "%d" % int(math.ceil(level.time_left)),
         theme.DANGER if level.time_left <= 10.0 else theme.SUCCESS),
    )
    for fraction, (label, value, color) in zip(columns, values):
        x = int(width * fraction)
        renderer.text(x, 8, label, theme.TEXT_DIM, 1)
        renderer.text(x, 22, value, color, 3)
    _draw_lives(renderer, session.lives)
    _draw_time_bar(renderer, level.time_left, level.max_time)


def _draw_lives(renderer: Renderer, lives: int) -> None:
    """Draw one small Pac-Man per remaining life."""
    size = 22
    right = renderer.width - theme.MARGIN
    renderer.text_right(right, 8, "LIVES", theme.TEXT_DIM, 1)
    shown = min(lives, 5)
    for index in range(shown):
        x = right - (index + 1) * (size + 6)
        sprites.draw_life_icon(renderer.frame, x, 24, size)
    if lives > shown:
        renderer.text_right(right - shown * (size + 6) - 6, 28,
                            "+%d" % (lives - shown), theme.TEXT_DIM, 2)


def _draw_time_bar(renderer: Renderer, left: float, total: float) -> None:
    """Draw the thin progress bar showing the level clock."""
    if total <= 0.0:
        return
    width = renderer.width
    ratio = max(0.0, min(1.0, left / total))
    color = theme.DANGER if ratio < 0.15 else theme.WALL_EDGE
    renderer.frame.fill_rect(0, theme.HUD_HEIGHT - 6, width, 4,
                             theme.BACKGROUND)
    renderer.frame.fill_rect(0, theme.HUD_HEIGHT - 6, int(width * ratio), 4,
                             color)


def draw_cheat_panel(renderer: Renderer, cheats: Cheats) -> None:
    """List the cheat switches at the bottom of the screen."""
    if not cheats.enabled:
        _draw_footer(renderer, "F1 CHEAT MODE     P PAUSE     ESC PAUSE")
        return
    entries = cheats.summary()
    parts = ["F1 CHEATS ON"]
    for key, label, active in entries:
        parts.append("%s %s%s" % (key, label, " *" if active else ""))
    _draw_footer(renderer, "   ".join(parts), theme.SUCCESS)


def _draw_footer(renderer: Renderer, message: str,
                 color: int = theme.TEXT_DIM) -> None:
    """Draw the one-line hint bar at the bottom of the window."""
    top = renderer.height - theme.FOOTER_HEIGHT
    renderer.frame.fill_rect(0, top, renderer.width, theme.FOOTER_HEIGHT,
                             theme.PANEL)
    renderer.text_center(top + 10, message, color, 1)


def draw_pause(renderer: Renderer, selection: int) -> None:
    """Draw the pause overlay on top of the frozen board."""
    renderer.dim_screen(0.3)
    width = int(renderer.width * 0.52)
    height = int(renderer.height * 0.34)
    left = (renderer.width - width) // 2
    top = (renderer.height - height) // 2
    renderer.frame.fill_rect(left, top, width, height, theme.PANEL)
    renderer.frame.rect_outline(left, top, width, height, theme.ACCENT, 2)
    renderer.text_center(top + 24, "PAUSED", theme.ACCENT, 4)
    for index, label in enumerate(PAUSE_ITEMS):
        color = theme.ACCENT if index == selection else theme.TEXT
        renderer.text_center(top + 96 + index * 46, label, color, 2)
    renderer.text_center(top + height - 30,
                         "P OR ESC RESUMES", theme.TEXT_DIM, 1)


def draw_name_entry(renderer: Renderer, session: Session, name: str,
                    qualifies: bool, clock: float) -> None:
    """Draw the game-over / victory screen and its name prompt."""
    renderer.dim_screen(0.25)
    won = session.won
    title = "YOU WIN!" if won else "GAME OVER"
    color = theme.SUCCESS if won else theme.DANGER
    width = int(renderer.width * 0.66)
    height = int(renderer.height * 0.46)
    left = (renderer.width - width) // 2
    top = (renderer.height - height) // 2
    renderer.frame.fill_rect(left, top, width, height, theme.PANEL)
    renderer.frame.rect_outline(left, top, width, height, color, 2)
    renderer.text_center(top + 26, title, color, 5)
    if won:
        renderer.text_center(top + 92, "EVERY LEVEL CLEARED - WAKA WAKA!",
                             theme.TEXT, 1)
    renderer.text_center(top + 116, "FINAL SCORE", theme.TEXT_DIM, 1)
    renderer.text_center(top + 134, str(session.score), theme.ACCENT, 4)
    prompt = "ENTER YOUR NAME" if qualifies else "NAME (NOT IN TOP 10)"
    renderer.text_center(top + 200, prompt, theme.TEXT_DIM, 1)
    caret = "_" if int(clock * 2.0) % 2 == 0 else " "
    shown = name + (caret if len(name) < MAX_NAME_LENGTH else "")
    renderer.text_center(top + 220, shown or caret, theme.TEXT, 4)
    renderer.text_center(top + height - 34,
                         "LETTERS AND SPACES, 10 MAX     ENTER TO SAVE",
                         theme.TEXT_DIM, 1)


def draw_message_screen(renderer: Renderer, title: str,
                        lines: Sequence[str], color: int = theme.DANGER,
                        footer: str = "ESC TO QUIT") -> None:
    """Draw a plain centred message; used for fatal start-up errors."""
    renderer.clear()
    renderer.text_center(int(renderer.height * 0.28), title, color, 4)
    row = int(renderer.height * 0.44)
    for line in lines:
        renderer.text_center(row, line, theme.TEXT, 1)
        row += 22
    _draw_footer(renderer, footer)


def draw_warnings(renderer: Renderer, warnings: Sequence[str]) -> None:
    """Draw the configuration warnings collected at start-up."""
    renderer.clear()
    renderer.text_center(int(renderer.height * 0.08),
                         "CONFIGURATION NOTICES", theme.ACCENT, 3)
    renderer.text_center(int(renderer.height * 0.15),
                         "THE GAME STARTED WITH SAFE DEFAULTS",
                         theme.TEXT_DIM, 1)
    row = int(renderer.height * 0.24)
    for line in warnings[:18]:
        renderer.text(int(renderer.width * 0.08), row, line.upper()[:96],
                      theme.TEXT, 1)
        row += 22
    if len(warnings) > 18:
        renderer.text(int(renderer.width * 0.08), row,
                      "... AND %d MORE" % (len(warnings) - 18),
                      theme.TEXT_DIM, 1)
    _draw_footer(renderer, "ENTER OR ESC TO CONTINUE")
