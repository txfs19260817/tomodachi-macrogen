from collections.abc import Iterable
from typing import Any

from .glams_format import MacroLine, format_controller_state, format_stick, normalize_button
from .splitter import split_macro_lines


class MacroWriter:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.timing = self.config.get("timing", {})
        self.lines: list[MacroLine] = []
        self.current_x = int(self.config.get("canvas_origin_x", 0))
        self.current_y = int(self.config.get("canvas_origin_y", 0))

    def tap(
        self,
        button: str | Iterable[str],
        hold_frames: int | None = None,
        release_frames: int | None = None,
    ) -> None:
        hold = hold_frames or int(self.timing.get("tap_hold_frames", 2))
        release = release_frames or int(self.timing.get("tap_release_frames", 1))
        self.hold(button, hold)
        self.release(release)

    def hold(self, buttons: str | Iterable[str], frames: int) -> None:
        self.lines.append(format_controller_state(buttons, frames))

    def release(self, frames: int) -> None:
        self.lines.append(format_controller_state(None, frames, safe_split_after=True))

    def wait(self, frames: int) -> None:
        self.release(frames)

    def dpad(self, direction: str, steps: int) -> None:
        normalized = normalize_button(direction)
        if normalized not in {"U", "D", "L", "R"}:
            raise ValueError("direction must be one of U, D, L, R")
        hold = int(self.timing.get("movement_hold_frames", 1))
        release = int(self.timing.get("movement_release_frames", 1))
        for _ in range(max(0, steps)):
            self.tap(normalized, hold, release)

    def stick(self, lx: int, ly: int, rx: int, ry: int, frames: int) -> None:
        neutral = self._neutral_stick()
        safe = (lx, ly, rx, ry) == (neutral, neutral, neutral, neutral)
        self.lines.append(format_stick(lx, ly, rx, ry, frames, safe_split_after=safe))

    def move_cursor_to(self, x: int, y: int) -> None:
        target_x = int(x) + int(self.config.get("canvas_origin_x", 0))
        target_y = int(y) + int(self.config.get("canvas_origin_y", 0))

        dx = target_x - self.current_x
        dy = target_y - self.current_y
        if dx > 0:
            self._move_canvas_direction("R", dx)
        elif dx < 0:
            self._move_canvas_direction("L", -dx)
        if dy > 0:
            self._move_canvas_direction("D", dy)
        elif dy < 0:
            self._move_canvas_direction("U", -dy)

        self.current_x = target_x
        self.current_y = target_y

    def draw_pixel(self) -> None:
        hold = int(self.timing.get("draw_hold_frames", self.timing.get("tap_hold_frames", 2)))
        release = int(
            self.timing.get("draw_release_frames", self.timing.get("tap_release_frames", 1))
        )
        self.tap("A", hold, release)

    def split_output(
        self,
        max_lines_per_part: int | None = None,
        max_frames_per_part: int | None = None,
    ) -> list[list[str]]:
        return split_macro_lines(self.lines, max_lines_per_part, max_frames_per_part)

    def total_frames(self) -> int:
        return sum(line.frames for line in self.lines)

    def _move_canvas_direction(self, direction: str, steps: int) -> None:
        hold = int(self.timing.get("movement_hold_frames", 1))
        release = int(self.timing.get("movement_release_frames", 1))
        for _ in range(steps):
            self.tap(direction, hold, release)

    def _neutral_stick(self) -> int:
        return int(self.config.get("stick", {}).get("neutral", 128))
