from typing import Any

from .living_grid import PressCounts
from .macro_writer import MacroWriter


class ColorPicker:
    """Emit Tomodachi Life picker navigation through SwiCC macro inputs.

    The algorithm follows the user-provided spec and is aligned with
    TomodachiDraw's CanvasNavigatorService.cs:
    https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/CanvasNavigatorService.cs
    """

    def __init__(self, writer: MacroWriter, config: dict[str, Any]) -> None:
        self.writer = writer
        self.config = config
        self.timing = config.get("timing", {})
        self.palette_slots = int(config.get("palette_slots", 9))
        self.active_palette_slot: int | None = None

    def set_palette_slot_press(self, slot_index: int, press: PressCounts) -> None:
        self._validate_slot(slot_index)

        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("menu_open_frames", 8)))
        self.navigate_to_slot(slot_index)
        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("R1")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.reset_picker_to_default()
        self._move_hue_to_press_count(press.h)
        self._move_colour_rect_to_press_count(press.s, press.b)
        self.writer.tap("A")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("B")
        self.writer.wait(int(self.timing.get("menu_close_frames", 8)))
        self.active_palette_slot = None

    def set_current_palette_slot_press(self, press: PressCounts) -> None:
        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("menu_open_frames", 8)))
        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("R1")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.reset_picker_to_default()
        self._move_hue_to_press_count(press.h)
        self._move_colour_rect_to_press_count(press.s, press.b)
        self.writer.tap("A")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("B")
        self.writer.wait(int(self.timing.get("menu_close_frames", 8)))
        self.active_palette_slot = None

    def navigate_to_slot(self, slot_index: int) -> None:
        self._validate_slot(slot_index)
        self.writer.hold("D", int(self.timing.get("slot_anchor_hold_frames", 18)))
        self.writer.release(int(self.timing.get("slot_anchor_release_frames", 2)))
        self.writer.wait(int(self.timing.get("slot_settle_frames", 2)))

        steps_up = self.palette_slots - 1 - slot_index
        hold = int(self.timing.get("slot_step_hold_frames", 2))
        release = int(self.timing.get("slot_step_release_frames", 1))
        for _ in range(steps_up):
            self.writer.tap("U", hold, release)
        self.writer.wait(int(self.timing.get("slot_settle_frames", 2)))

    def set_hue_press_count(self, press_count: int) -> None:
        self.writer.hold("L2", int(self.timing.get("hue_anchor_hold_frames", 30)))
        self.writer.release(int(self.timing.get("hue_anchor_release_frames", 2)))
        self._move_hue_to_press_count(press_count)

    def _move_hue_to_press_count(self, press_count: int) -> None:
        max_hue = max(0, int(self.config.get("hue_slider_steps", 202)) - 1)
        hue = max(0, min(max_hue, press_count))
        hold = int(self.timing.get("hue_step_hold_frames", 2))
        release = int(self.timing.get("hue_step_release_frames", 1))
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

    def _move_colour_rect_to_press_count(
        self,
        saturation_presses: int,
        brightness_presses: int,
    ) -> None:
        max_saturation = max(0, int(self.config.get("colour_rect_width", 212)) - 1)
        saturation = max(0, min(max_saturation, saturation_presses))
        max_brightness = max(0, int(self.config.get("colour_rect_height", 111)) - 1)
        brightness = max(0, min(max_brightness, brightness_presses))
        hold = int(self.timing.get("colour_rect_step_hold_frames", 1))
        release = int(self.timing.get("colour_rect_step_release_frames", 1))

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
        self.writer.wait(int(self.timing.get("menu_open_frames", 8)))
        self.navigate_to_slot(slot_index)
        self.writer.tap("A")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("B")
        self.writer.wait(int(self.timing.get("menu_close_frames", 8)))
        self.active_palette_slot = slot_index

    def reset_picker_to_default(self) -> None:
        self._anchor_colour_rect_bottom_left(reset_hue=True)

    def _anchor_hue_right(self) -> None:
        self.writer.hold("R2", int(self.timing.get("hue_anchor_hold_frames", 30)))
        self.writer.release(int(self.timing.get("hue_anchor_release_frames", 2)))

    def _anchor_colour_rect_bottom_left(self, *, reset_hue: bool) -> None:
        method = str(self.config.get("anchor_colour_rect_method", "analog"))
        hold_frames = int(self.timing.get("colour_rect_anchor_hold_frames", 45))
        settle_frames = int(self.timing.get("colour_rect_anchor_settle_frames", 4))
        neutral = int(self.config.get("stick", {}).get("neutral", 128))
        stick_min = int(self.config.get("stick", {}).get("min", 0))
        stick_max = int(self.config.get("stick", {}).get("max", 255))
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
                self.writer.hold("L2", int(self.timing.get("hue_anchor_hold_frames", 30)))
                self.writer.release(int(self.timing.get("hue_anchor_release_frames", 2)))
            self.writer.dpad("L", int(self.config.get("colour_rect_width", 212)))
            self.writer.dpad("D", int(self.config.get("colour_rect_height", 111)))
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
        method = str(self.config.get("anchor_colour_rect_method", "analog"))
        hold_frames = int(self.timing.get("colour_rect_anchor_hold_frames", 45))
        settle_frames = int(self.timing.get("colour_rect_anchor_settle_frames", 4))
        neutral = int(self.config.get("stick", {}).get("neutral", 128))
        stick_min = int(self.config.get("stick", {}).get("min", 0))
        stick_max = int(self.config.get("stick", {}).get("max", 255))
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
            self.writer.dpad(horizontal, int(self.config.get("colour_rect_width", 212)))
            self.writer.dpad(vertical, int(self.config.get("colour_rect_height", 111)))
            self.writer.wait(settle_frames)
            return
        raise ValueError(
            "anchor_colour_rect_method must be 'analog', 'dpad_hold', or 'dpad_steps'"
        )

    def _validate_slot(self, slot_index: int) -> None:
        if slot_index < 0 or slot_index >= self.palette_slots:
            raise ValueError(f"slot_index must be in range 0..{self.palette_slots - 1}")
