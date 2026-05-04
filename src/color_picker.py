from dataclasses import dataclass

from .config import ConfigInput, as_app_config
from .living_grid import GamePaletteTarget, PressCounts
from .macro_writer import MacroWriter


@dataclass(frozen=True)
class GamePalettePosition:
    row: int
    col: int


class ColorPicker:
    """Emit Tomodachi Life picker navigation through SwiCC macro inputs.

    The algorithm follows the user-provided spec and is aligned with
    TomodachiDraw's CanvasNavigatorService.cs:
    https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/CanvasNavigatorService.cs
    """

    def __init__(
        self,
        writer: MacroWriter,
        config: ConfigInput,
        *,
        game_palette_position: GamePalettePosition | None = None,
    ) -> None:
        self.writer = writer
        self.config = as_app_config(config)
        self.timing = self.config.timing
        self.palette_slots = self.config.palette_slots
        self.active_palette_slot: int | None = None
        self.game_palette_position = game_palette_position or self._initial_game_palette_position()

    def set_palette_slot_press(self, slot_index: int, press: PressCounts) -> None:
        self._validate_slot(slot_index)

        self.writer.tap("Y")
        self.writer.wait(self.timing.menu_open_frames)
        self.navigate_to_slot(slot_index)
        self.writer.tap("Y")
        self.writer.wait(self.timing.screen_settle_frames)
        self.writer.tap("R1")
        self.writer.wait(self.timing.screen_settle_frames)
        self.reset_picker_to_default()
        self._move_hue_to_press_count(press.h)
        self._move_colour_rect_to_press_count(press.s, press.b)
        self.writer.tap("A")
        self.writer.wait(self.timing.screen_settle_frames)
        self.writer.tap("B")
        self.writer.wait(self.timing.menu_close_frames)
        self.active_palette_slot = None

    def set_current_palette_slot_press(self, press: PressCounts) -> None:
        self.writer.tap("Y")
        self.writer.wait(self.timing.menu_open_frames)
        self.writer.tap("Y")
        self.writer.wait(self.timing.screen_settle_frames)
        self.writer.tap("R1")
        self.writer.wait(self.timing.screen_settle_frames)
        self.reset_picker_to_default()
        self._move_hue_to_press_count(press.h)
        self._move_colour_rect_to_press_count(press.s, press.b)
        self.writer.tap("A")
        self.writer.wait(self.timing.screen_settle_frames)
        self.writer.tap("B")
        self.writer.wait(self.timing.menu_close_frames)
        self.active_palette_slot = None

    def set_current_palette_slot_game(self, target: GamePaletteTarget) -> None:
        self.writer.tap("Y")
        self.writer.wait(self.timing.menu_open_frames)
        self.writer.tap("Y")
        self.writer.wait(self.timing.screen_settle_frames)
        self.writer.tap("L1")
        self.writer.wait(self.timing.screen_settle_frames)
        self.navigate_game_palette_target(target)
        self.writer.tap("A")
        self.writer.wait(self.timing.screen_settle_frames)
        self.writer.tap("B")
        self.writer.wait(self.timing.menu_close_frames)
        self.active_palette_slot = None

    def navigate_to_slot(self, slot_index: int) -> None:
        self._validate_slot(slot_index)
        self.writer.hold("D", self.timing.slot_anchor_hold_frames)
        self.writer.release(self.timing.slot_anchor_release_frames)
        self.writer.wait(self.timing.slot_settle_frames)

        steps_up = self.palette_slots - 1 - slot_index
        hold = self.timing.slot_step_hold_frames
        release = self.timing.slot_step_release_frames
        for _ in range(steps_up):
            self.writer.tap("U", hold, release)
        self.writer.wait(self.timing.slot_settle_frames)

    def set_hue_press_count(self, press_count: int) -> None:
        self.writer.hold("L2", self.timing.hue_anchor_hold_frames)
        self.writer.release(self.timing.hue_anchor_release_frames)
        self._move_hue_to_press_count(press_count)

    def _move_hue_to_press_count(self, press_count: int) -> None:
        max_hue = max(0, self.config.hue_slider_steps - 1)
        hue = max(0, min(max_hue, press_count))
        hold = self.timing.hue_step_hold_frames
        release = self.timing.hue_step_release_frames
        left_distance = hue
        right_distance = max_hue - hue
        if right_distance < left_distance:
            self._anchor_hue_right()
            for _ in range(right_distance):
                self.writer.tap("L2", hold, release)
            return
        for _ in range(left_distance):
            self.writer.tap("R2", hold, release)

    def set_colour_rect_press_count(self, saturation_presses: int, brightness_presses: int) -> None:
        self._anchor_colour_rect_bottom_left(reset_hue=False)
        self._move_colour_rect_to_press_count(saturation_presses, brightness_presses)

    def navigate_game_palette_target(self, target: GamePaletteTarget) -> None:
        self._move_game_palette_to_position(self._target_game_palette_position(target))

    def _move_colour_rect_to_press_count(
        self,
        saturation_presses: int,
        brightness_presses: int,
    ) -> None:
        max_saturation = max(0, self.config.colour_rect_width - 1)
        saturation = max(0, min(max_saturation, saturation_presses))
        max_brightness = max(0, self.config.colour_rect_height - 1)
        brightness = max(0, min(max_brightness, brightness_presses))
        hold = self.timing.colour_rect_step_hold_frames
        release = self.timing.colour_rect_step_release_frames

        left_distance = saturation
        right_distance = max_saturation - saturation
        bottom_distance = brightness
        top_distance = max_brightness - brightness
        use_right_anchor = right_distance < left_distance
        use_top_anchor = top_distance < bottom_distance

        if use_right_anchor and use_top_anchor:
            self._anchor_colour_rect_top_right()
        elif use_right_anchor:
            self._anchor_colour_rect_bottom_right()
        elif use_top_anchor:
            self._anchor_colour_rect_top_left()

        if use_right_anchor:
            for _ in range(right_distance):
                self.writer.tap("L", hold, release)
        else:
            for _ in range(left_distance):
                self.writer.tap("R", hold, release)

        if use_top_anchor:
            for _ in range(top_distance):
                self.writer.tap("D", hold, release)
        else:
            for _ in range(bottom_distance):
                self.writer.tap("U", hold, release)

    def activate_palette_slot(self, slot_index: int, *, force: bool = False) -> None:
        self._validate_slot(slot_index)
        if not force and self.active_palette_slot == slot_index:
            return

        self.writer.tap("Y")
        self.writer.wait(self.timing.menu_open_frames)
        self.navigate_to_slot(slot_index)
        self.writer.tap("A")
        self.writer.wait(self.timing.screen_settle_frames)
        self.writer.tap("B")
        self.writer.wait(self.timing.menu_close_frames)
        self.active_palette_slot = slot_index

    def reset_picker_to_default(self) -> None:
        self._anchor_colour_rect_bottom_left(reset_hue=True)

    def _anchor_hue_right(self) -> None:
        self.writer.hold("R2", self.timing.hue_anchor_hold_frames)
        self.writer.release(self.timing.hue_anchor_release_frames)

    def _anchor_colour_rect_bottom_left(self, *, reset_hue: bool) -> None:
        method = self.config.anchor_colour_rect_method
        hold_frames = self.timing.colour_rect_anchor_hold_frames
        settle_frames = self.timing.colour_rect_anchor_settle_frames
        neutral = self.config.stick.neutral
        stick_min = self.config.stick.min
        stick_max = self.config.stick.max
        buttons = "L2" if reset_hue else None

        if method == "analog":
            self.writer.stick(
                stick_min,
                stick_max,
                neutral,
                neutral,
                hold_frames,
                buttons=buttons,
            )
            self.writer.stick(neutral, neutral, neutral, neutral, settle_frames)
            return
        if method == "dpad_hold":
            held = ["L", "D"]
            if reset_hue:
                held.append("L2")
            self.writer.hold(held, hold_frames)
            self.writer.release(settle_frames)
            return
        if method == "dpad_steps":
            if reset_hue:
                self.writer.hold("L2", self.timing.hue_anchor_hold_frames)
                self.writer.release(self.timing.hue_anchor_release_frames)
            self.writer.dpad("L", self.config.colour_rect_width)
            self.writer.dpad("D", self.config.colour_rect_height)
            self.writer.wait(settle_frames)
            return
        raise ValueError(
            "anchor_colour_rect_method must be 'analog', 'dpad_hold', or 'dpad_steps'"
        )

    def _anchor_colour_rect_bottom_right(self) -> None:
        self._anchor_colour_rect_corner("R", "D")

    def _anchor_colour_rect_top_left(self) -> None:
        self._anchor_colour_rect_corner("L", "U")

    def _anchor_colour_rect_top_right(self) -> None:
        self._anchor_colour_rect_corner("R", "U")

    def _anchor_colour_rect_corner(self, horizontal: str, vertical: str) -> None:
        method = self.config.anchor_colour_rect_method
        hold_frames = self.timing.colour_rect_anchor_hold_frames
        settle_frames = self.timing.colour_rect_anchor_settle_frames
        neutral = self.config.stick.neutral
        stick_min = self.config.stick.min
        stick_max = self.config.stick.max
        lx = stick_max if horizontal == "R" else stick_min
        ly = stick_min if vertical == "U" else stick_max

        if method == "analog":
            self.writer.stick(lx, ly, neutral, neutral, hold_frames)
            self.writer.stick(neutral, neutral, neutral, neutral, settle_frames)
            return
        if method == "dpad_hold":
            self.writer.hold([horizontal, vertical], hold_frames)
            self.writer.release(settle_frames)
            return
        if method == "dpad_steps":
            self.writer.dpad(horizontal, self.config.colour_rect_width)
            self.writer.dpad(vertical, self.config.colour_rect_height)
            self.writer.wait(settle_frames)
            return
        raise ValueError(
            "anchor_colour_rect_method must be 'analog', 'dpad_hold', or 'dpad_steps'"
        )

    def _validate_slot(self, slot_index: int) -> None:
        if slot_index < 0 or slot_index >= self.palette_slots:
            raise ValueError(f"slot_index must be in range 0..{self.palette_slots - 1}")

    def _initial_game_palette_position(self) -> GamePalettePosition:
        return GamePalettePosition(row=self.config.game_palette_rows, col=1)

    def _target_game_palette_position(self, target: GamePaletteTarget) -> GamePalettePosition:
        rows = self.config.game_palette_rows
        cols = self.config.game_palette_cols
        extras = self.config.game_palette_extras
        if target.kind == "grid":
            if (
                target.col is None
                or target.row < 1
                or target.row > rows
                or target.col < 1
                or target.col > cols
            ):
                raise ValueError(f"game palette grid target is outside {rows}x{cols}")
            return GamePalettePosition(row=target.row, col=target.col)
        if target.kind == "extra":
            if target.row < 1 or target.row > extras:
                raise ValueError(f"game palette extra target is outside 1..{extras}")
            return GamePalettePosition(row=target.row, col=cols + 1)
        raise ValueError("game palette target kind must be 'grid' or 'extra'")

    def _move_game_palette_to_position(self, target: GamePalettePosition) -> None:
        current = self.game_palette_position
        horizontal_steps = target.col - current.col
        if horizontal_steps > 0:
            self.writer.dpad("R", horizontal_steps)
        elif horizontal_steps < 0:
            self.writer.dpad("L", -horizontal_steps)

        vertical_direction, vertical_steps = self._shortest_vertical_game_palette_move(
            current.row,
            target.row,
        )
        self.writer.dpad(vertical_direction, vertical_steps)
        self.game_palette_position = target

    def _shortest_vertical_game_palette_move(
        self,
        current_row: int,
        target_row: int,
    ) -> tuple[str, int]:
        rows = self.config.game_palette_rows
        down_steps = (target_row - current_row) % rows
        up_steps = (current_row - target_row) % rows
        if up_steps < down_steps:
            return "U", up_steps
        return "D", down_steps
