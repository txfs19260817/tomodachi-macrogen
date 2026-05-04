from collections.abc import Iterable

from .config import ConfigInput, as_app_config
from .splitter import split_macro_lines
from .swicc_format import (
    MacroLine,
    format_controller_state,
    format_stick,
    normalize_button,
)


class MacroWriter:
    def __init__(self, config: ConfigInput = None) -> None:
        self.config = as_app_config(config)
        self.timing = self.config.timing
        self.canvas_cell_step = self.config.effective_canvas_cell_step
        if self.canvas_cell_step < 1:
            raise ValueError("canvas_cell_step must be greater than zero")
        self.lines: list[MacroLine] = []
        self.current_x = self.config.canvas_origin_x
        self.current_y = self.config.canvas_origin_y
        self.draw_events: list[tuple[int, int]] = []

    def tap(
        self,
        button: str | Iterable[str],
        hold_frames: int | None = None,
        release_frames: int | None = None,
    ) -> None:
        hold = hold_frames or self.timing.tap_hold_frames
        release = release_frames or self.timing.tap_release_frames
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
        hold = self.timing.movement_hold_frames
        release = self.timing.movement_release_frames
        for _ in range(max(0, steps)):
            self.tap(normalized, hold, release)

    def stick(
        self,
        lx: int,
        ly: int,
        rx: int,
        ry: int,
        frames: int,
        *,
        buttons: str | Iterable[str] | None = None,
    ) -> None:
        neutral = self._neutral_stick()
        safe = (lx, ly, rx, ry) == (neutral, neutral, neutral, neutral)
        self.lines.append(
            format_stick(lx, ly, rx, ry, frames, buttons=buttons, safe_split_after=safe)
        )

    def move_cursor_to(self, x: int, y: int) -> None:
        target_x = int(x) + self.config.canvas_origin_x
        target_y = int(y) + self.config.canvas_origin_y

        dx = target_x - self.current_x
        dy = target_y - self.current_y
        if dx > 0:
            self._move_canvas_direction("R", dx * self.canvas_cell_step)
        elif dx < 0:
            self._move_canvas_direction("L", -dx * self.canvas_cell_step)
        if dy > 0:
            self._move_canvas_direction("D", dy * self.canvas_cell_step)
        elif dy < 0:
            self._move_canvas_direction("U", -dy * self.canvas_cell_step)

        self.current_x = target_x
        self.current_y = target_y

    def reset_canvas_to_origin(self) -> None:
        neutral = self._neutral_stick()
        stick_min = self.config.stick.min
        hold_frames = self.timing.canvas_reset_hold_frames
        settle_frames = self.timing.canvas_reset_settle_frames
        right_steps = self.config.canvas_reset_right_steps
        down_steps = self.config.canvas_reset_down_steps

        self.stick(stick_min, stick_min, neutral, neutral, hold_frames)
        self.stick(neutral, neutral, neutral, neutral, settle_frames)
        self._move_canvas_direction("R", right_steps)
        self._move_canvas_direction("D", down_steps)
        self.current_x = self.config.canvas_origin_x
        self.current_y = self.config.canvas_origin_y

    def canvas_position(self) -> tuple[int, int]:
        return (
            self.current_x - self.config.canvas_origin_x,
            self.current_y - self.config.canvas_origin_y,
        )

    def draw_pixels(self, points: Iterable[tuple[int, int]]) -> None:
        current_run: list[tuple[int, int]] = []
        for point in points:
            if current_run and self._continues_horizontal_run(current_run[-1], point):
                current_run.append(point)
                continue
            self._draw_run(current_run)
            current_run = [point]
        self._draw_run(current_run)

    def draw_pixel(self) -> None:
        self.draw_events.append(self.canvas_position())
        hold = self.timing.draw_hold_frames
        release = self.timing.draw_release_frames
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
        hold = self.timing.movement_hold_frames
        release = self.timing.movement_release_frames
        chunk_size = self.timing.movement_chunk_size
        chunk_settle = self.timing.movement_chunk_settle_frames
        for step in range(steps):
            self.tap(direction, hold, release)
            if chunk_size > 0 and chunk_settle > 0 and step + 1 < steps:
                if (step + 1) % chunk_size == 0:
                    self.wait(chunk_settle)

    def _neutral_stick(self) -> int:
        return self.config.stick.neutral

    def _draw_run(self, points: list[tuple[int, int]]) -> None:
        if not points:
            return
        self.move_cursor_to(*points[0])
        if len(points) == 1:
            self.draw_pixel()
            return

        hold = self.timing.draw_hold_frames
        release = self.timing.draw_release_frames
        self.draw_events.append(self.canvas_position())
        self.hold("A", hold)
        previous = points[0]
        for point in points[1:]:
            direction = self._horizontal_step_direction(previous, point)
            self._drag_canvas_direction(direction)
            previous = point
        self.release(release)

    def _drag_canvas_direction(self, direction: str) -> None:
        normalized = normalize_button(direction)
        if normalized not in {"L", "R"}:
            raise ValueError("drag direction must be L or R")

        hold = self.timing.movement_hold_frames
        release = self.timing.movement_release_frames
        chunk_size = self.timing.movement_chunk_size
        chunk_settle = self.timing.movement_chunk_settle_frames

        for _ in range(self.canvas_cell_step):
            self.hold(["A", normalized], hold)
            self.hold("A", release)
        if normalized == "R":
            self.current_x += 1
        else:
            self.current_x -= 1
        self.draw_events.append(self.canvas_position())
        if chunk_size > 0 and chunk_settle > 0 and len(self.draw_events) % chunk_size == 0:
            self.hold("A", chunk_settle)

    @staticmethod
    def _continues_horizontal_run(
        previous: tuple[int, int],
        current: tuple[int, int],
    ) -> bool:
        return previous[1] == current[1] and abs(previous[0] - current[0]) == 1

    @staticmethod
    def _horizontal_step_direction(previous: tuple[int, int], current: tuple[int, int]) -> str:
        if previous[1] != current[1] or abs(previous[0] - current[0]) != 1:
            raise ValueError("drag draw only supports adjacent horizontal pixels")
        return "R" if current[0] > previous[0] else "L"
