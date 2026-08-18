"""The application: screens, input routing and the main loop."""

from enum import Enum
from typing import Optional, Sequence

from .game import direction as compass
from .game.cheats import Cheats
from .game.direction import Direction
from .game.session import Session, SessionState, new_session
from .highscore import Highscores, MAX_NAME_LENGTH, is_name_char
from .mlxlib import Mlx, MlxError, keys
from .settings import Config
from .ui import screens
from .ui.render import Renderer

WINDOW_TITLE = "Pac-Man - Ghosts! More ghosts!"

_STEERING: dict[int, Direction] = {
    keys.KEY_UP: compass.UP,
    keys.KEY_DOWN: compass.DOWN,
    keys.KEY_LEFT: compass.LEFT,
    keys.KEY_RIGHT: compass.RIGHT,
    ord("w"): compass.UP,
    ord("W"): compass.UP,
    ord("s"): compass.DOWN,
    ord("S"): compass.DOWN,
    ord("a"): compass.LEFT,
    ord("A"): compass.LEFT,
    ord("d"): compass.RIGHT,
    ord("D"): compass.RIGHT,
}

_MENU_UP = (keys.KEY_UP, ord("w"), ord("W"))
_MENU_DOWN = (keys.KEY_DOWN, ord("s"), ord("S"))
_VALIDATE = (keys.KEY_RETURN, keys.KEY_SPACE)


class Screen(Enum):
    """Which view currently owns the window."""

    WARNINGS = "warnings"
    MENU = "menu"
    HIGHSCORES = "highscores"
    INSTRUCTIONS = "instructions"
    GAME = "game"
    PAUSED = "paused"
    NAME_ENTRY = "name-entry"
    FATAL = "fatal"


class Application:
    """Owns the window, the current screen and the running session."""

    def __init__(self, config: Config,
                 warnings: Sequence[str] = ()) -> None:
        """Prepare the application without opening the window yet."""
        self.config = config
        self.warnings = list(warnings)
        self.cheats = Cheats(enabled=config.cheat_mode)
        self.scores = Highscores(config.highscore_path,
                                 config.highscore_size)
        self.warnings.extend(self.scores.load())
        self.screen = Screen.WARNINGS if self.warnings else Screen.MENU
        self.selection = 0
        self.pause_selection = 0
        self.session: Optional[Session] = None
        self.notice = ""
        self.name = ""
        self.qualifies = False
        self.clock = 0.0
        self.fatal: list[str] = []
        self._mlx: Optional[Mlx] = None
        self._renderer: Optional[Renderer] = None

    def run(self) -> int:
        """Open the window and run until the player quits."""
        try:
            mlx = Mlx(self.config.backend)
            mlx.set_target_fps(self.config.target_fps)
            mlx.new_window(self.config.window_width,
                           self.config.window_height, WINDOW_TITLE)
        except MlxError as error:
            print("error: %s" % error)
            return 1
        self._mlx = mlx
        self._renderer = Renderer(mlx, self.config.window_width,
                                  self.config.window_height)
        mlx.key_hook(self.on_key)
        mlx.hook(keys.EVENT_DESTROY, keys.MASK_STRUCTURE_NOTIFY,
                 self.on_destroy)
        mlx.loop_hook(self.on_frame)
        try:
            mlx.loop()
        finally:
            mlx.destroy_window()
        return 0

    def quit(self) -> None:
        """Leave the main loop."""
        if self._mlx is not None:
            self._mlx.loop_end()

    def on_destroy(self, _code: int) -> None:
        """Handle the window close button."""
        self.quit()

    def on_frame(self, delta: float) -> None:
        """Advance the game and draw one frame."""
        self.clock += delta
        if self.screen is Screen.GAME:
            self._advance(delta)
        self._draw()

    def on_key(self, code: int) -> None:
        """Route a key press to the screen that currently has focus."""
        if self.screen is Screen.WARNINGS:
            self._key_warnings(code)
        elif self.screen is Screen.MENU:
            self._key_menu(code)
        elif self.screen in (Screen.HIGHSCORES, Screen.INSTRUCTIONS):
            if code in _VALIDATE or code == keys.KEY_ESCAPE:
                self.screen = Screen.MENU
        elif self.screen is Screen.GAME:
            self._key_game(code)
        elif self.screen is Screen.PAUSED:
            self._key_pause(code)
        elif self.screen is Screen.NAME_ENTRY:
            self._key_name(code)
        elif self.screen is Screen.FATAL:
            self.quit()

    def _advance(self, delta: float) -> None:
        """Tick the running session and react to its end."""
        session = self.session
        if session is None:
            self.screen = Screen.MENU
            return
        session.update(delta)
        if session.state is SessionState.FAILED:
            self.fatal = [session.error,
                          "The game cannot continue without a maze."]
            self.screen = Screen.FATAL
        elif session.is_over:
            self.name = ""
            self.qualifies = self.scores.qualifies(session.score)
            self.screen = Screen.NAME_ENTRY

    def _start_game(self) -> None:
        """Create a fresh session and jump into it."""
        session, error = new_session(self.config, self.cheats)
        if session is None:
            self.notice = error
            self.screen = Screen.MENU
            return
        self.session = session
        self.notice = ""
        self.screen = Screen.GAME
        if self._renderer is not None:
            self._renderer.prepare(session.level.maze)

    def _key_warnings(self, code: int) -> None:
        """Dismiss the configuration notices."""
        if code in _VALIDATE or code == keys.KEY_ESCAPE:
            self.screen = Screen.MENU

    def _key_menu(self, code: int) -> None:
        """Drive the main menu."""
        count = len(screens.MENU_ITEMS)
        if code in _MENU_UP:
            self.selection = (self.selection - 1) % count
        elif code in _MENU_DOWN:
            self.selection = (self.selection + 1) % count
        elif ord("1") <= code <= ord("0") + count:
            self.selection = code - ord("1")
            self._activate_menu()
        elif code in _VALIDATE:
            self._activate_menu()
        elif code == keys.KEY_ESCAPE:
            self.quit()

    def _activate_menu(self) -> None:
        """Run the highlighted main-menu entry."""
        if self.selection == 0:
            self._start_game()
        elif self.selection == 1:
            self.screen = Screen.HIGHSCORES
        elif self.selection == 2:
            self.screen = Screen.INSTRUCTIONS
        else:
            self.quit()

    def _key_game(self, code: int) -> None:
        """Drive the game view."""
        session = self.session
        if session is None:
            return
        heading = _STEERING.get(code)
        if heading is not None:
            session.level.player.steer(heading)
            return
        if code in (keys.KEY_ESCAPE, ord("p"), ord("P")):
            self.pause_selection = 0
            self.screen = Screen.PAUSED
            return
        self._key_cheat(code, session)

    def _key_cheat(self, code: int, session: Session) -> None:
        """Apply the cheat shortcuts."""
        if code == keys.KEY_F1:
            self.cheats.toggle_enabled()
            return
        if not self.cheats.enabled:
            return
        if code == keys.KEY_F2:
            self.cheats.invincible = not self.cheats.invincible
        elif code == keys.KEY_F3:
            self.cheats.frozen_ghosts = not self.cheats.frozen_ghosts
        elif code == keys.KEY_F4:
            self.cheats.fast_player = not self.cheats.fast_player
        elif code == keys.KEY_F5:
            self.cheats.show_targets = not self.cheats.show_targets
        elif code == keys.KEY_F6:
            session.level.skip()
        elif code == keys.KEY_F7:
            session.add_life()
        elif code == keys.KEY_F8:
            session.level.leave_one_pacgum()

    def _key_pause(self, code: int) -> None:
        """Drive the pause overlay."""
        count = len(screens.PAUSE_ITEMS)
        if code in _MENU_UP:
            self.pause_selection = (self.pause_selection - 1) % count
        elif code in _MENU_DOWN:
            self.pause_selection = (self.pause_selection + 1) % count
        elif code in (keys.KEY_ESCAPE, ord("p"), ord("P")):
            self.screen = Screen.GAME
        elif code in _VALIDATE:
            if self.pause_selection == 0:
                self.screen = Screen.GAME
            else:
                self.session = None
                self.screen = Screen.MENU

    def _key_name(self, code: int) -> None:
        """Collect the player name after a win or a loss."""
        if code == keys.KEY_BACKSPACE:
            self.name = self.name[:-1]
            return
        if code == keys.KEY_RETURN:
            self._save_score()
            return
        char = keys.to_char(code, shifted=True)
        if char and is_name_char(char) and len(self.name) < MAX_NAME_LENGTH:
            self.name += char

    def _save_score(self) -> None:
        """Store the score, then go back to the main menu."""
        session = self.session
        if session is not None:
            self.scores.add(self.name, session.score)
            problems = self.scores.save()
            self.notice = problems[0] if problems else ""
        self.session = None
        self.name = ""
        self.selection = 0
        self.screen = Screen.MENU

    def _draw(self) -> None:
        """Render the screen that currently has focus."""
        renderer = self._renderer
        if renderer is None:
            return
        if self.screen is Screen.WARNINGS:
            screens.draw_warnings(renderer, self.warnings)
        elif self.screen is Screen.MENU:
            screens.draw_menu(renderer, self.selection, self.scores,
                              self.notice, self.clock)
        elif self.screen is Screen.HIGHSCORES:
            screens.draw_highscores(renderer, self.scores, self.notice)
        elif self.screen is Screen.INSTRUCTIONS:
            screens.draw_instructions(renderer, self.config)
        elif self.screen is Screen.FATAL:
            screens.draw_message_screen(renderer, "SOMETHING WENT WRONG",
                                        self.fatal)
        else:
            self._draw_board(renderer)
        renderer.present()

    def _draw_board(self, renderer: Renderer) -> None:
        """Draw the maze plus whatever overlay sits on top of it."""
        session = self.session
        if session is None:
            self.screen = Screen.MENU
            return
        renderer.clear()
        renderer.draw_level(session.level, self.cheats, self.clock)
        screens.draw_hud(renderer, session, self.scores.best)
        screens.draw_cheat_panel(renderer, self.cheats)
        if self.screen is Screen.PAUSED:
            screens.draw_pause(renderer, self.pause_selection)
        elif self.screen is Screen.NAME_ENTRY:
            screens.draw_name_entry(renderer, session, self.name,
                                    self.qualifies, self.clock)
        else:
            renderer.banner(session)
