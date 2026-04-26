from typing import Any

from .living_grid import PressCounts
from .macro_writer import MacroWriter
from .palette import rgb_to_hsv

CALIBRATION_COLORS: list[tuple[str, tuple[int, int, int]]] = [
    ("red", (255, 0, 0)),
    ("orange", (255, 128, 0)),
    ("yellow", (255, 255, 0)),
    ("green", (0, 255, 0)),
    ("cyan", (0, 255, 255)),
    ("blue", (0, 0, 255)),
    ("purple", (128, 0, 255)),
    ("black", (0, 0, 0)),
    ("white", (255, 255, 255)),
]


class ColorPicker:
    """Emit Tomodachi Life picker navigation through GLaMS/SwiCC inputs.

    The algorithm follows the user-provided spec and is structured to be
    calibrated against TomodachiDraw's CanvasNavigatorService.cs:
    https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/CanvasNavigatorService.cs
    """

    def __init__(self, writer: MacroWriter, config: dict[str, Any]) -> None:
        self.writer = writer
        self.config = config
        self.timing = config.get("timing", {})
        self.palette_slots = int(config.get("palette_slots", 9))
        self.active_palette_slot: int | None = None

    def set_palette_slot_colour(self, slot_index: int, rgb: tuple[int, int, int]) -> None:
        self._validate_slot(slot_index)
        hue_degrees, saturation, brightness = rgb_to_hsv(rgb)

        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("menu_open_frames", 8)))
        self.navigate_to_slot(slot_index)
        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("R1")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.set_hue(hue_degrees)
        self.set_colour_rect(saturation, brightness)
        self.writer.tap("A")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("B")
        self.writer.wait(int(self.timing.get("menu_close_frames", 8)))
        self.active_palette_slot = None

    def set_palette_slot_press(self, slot_index: int, press: PressCounts) -> None:
        self._validate_slot(slot_index)

        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("menu_open_frames", 8)))
        self.navigate_to_slot(slot_index)
        self.writer.tap("Y")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.writer.tap("R1")
        self.writer.wait(int(self.timing.get("screen_settle_frames", 4)))
        self.set_hue_press_count(press.h)
        self.set_colour_rect_press_count(press.s, press.b)
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

    def set_hue(self, hue_degrees: float) -> None:
        hue_steps = int(self.config.get("hue_slider_steps", 200))
        target_step = int((hue_degrees % 360.0) / 360.0 * hue_steps)
        target_step = max(0, min(hue_steps, target_step))

        self.writer.hold("L2", int(self.timing.get("hue_anchor_hold_frames", 30)))
        self.writer.release(int(self.timing.get("hue_anchor_release_frames", 2)))
        hold = int(self.timing.get("hue_step_hold_frames", 2))
        release = int(self.timing.get("hue_step_release_frames", 1))
        for _ in range(target_step):
            self.writer.tap("R2", hold, release)

    def set_colour_rect(self, saturation: float, brightness: float) -> None:
        width = int(self.config.get("colour_rect_width", 212))
        height = int(self.config.get("colour_rect_height", 111))
        sat_x = int(max(0.0, min(1.0, saturation)) * width)
        bri_y = int((1.0 - max(0.0, min(1.0, brightness))) * height)
        sat_x = max(0, min(width, sat_x))
        bri_y = max(0, min(height, bri_y))

        self._anchor_colour_rect()
        hold = int(self.timing.get("colour_rect_step_hold_frames", 1))
        release = int(self.timing.get("colour_rect_step_release_frames", 1))
        for _ in range(sat_x):
            self.writer.tap("R", hold, release)
        for _ in range(bri_y):
            self.writer.tap("D", hold, release)

    def set_hue_press_count(self, press_count: int) -> None:
        self.writer.hold("L2", int(self.timing.get("hue_anchor_hold_frames", 30)))
        self.writer.release(int(self.timing.get("hue_anchor_release_frames", 2)))
        hold = int(self.timing.get("hue_step_hold_frames", 2))
        release = int(self.timing.get("hue_step_release_frames", 1))
        for _ in range(max(0, press_count)):
            self.writer.tap("R2", hold, release)

    def set_colour_rect_press_count(self, saturation_presses: int, brightness_presses: int) -> None:
        self._anchor_colour_rect_bottom_left()
        hold = int(self.timing.get("colour_rect_step_hold_frames", 1))
        release = int(self.timing.get("colour_rect_step_release_frames", 1))
        for _ in range(max(0, saturation_presses)):
            self.writer.tap("R", hold, release)
        for _ in range(max(0, brightness_presses)):
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

    def _anchor_colour_rect(self) -> None:
        method = str(self.config.get("anchor_colour_rect_method", "analog"))
        hold_frames = int(self.timing.get("colour_rect_anchor_hold_frames", 45))
        settle_frames = int(self.timing.get("colour_rect_anchor_settle_frames", 4))
        neutral = int(self.config.get("stick", {}).get("neutral", 128))
        stick_min = int(self.config.get("stick", {}).get("min", 0))

        if method == "analog":
            self.writer.stick(stick_min, stick_min, neutral, neutral, hold_frames)
            self.writer.stick(neutral, neutral, neutral, neutral, settle_frames)
            return
        if method == "dpad_hold":
            self.writer.hold(["L", "U"], hold_frames)
            self.writer.release(settle_frames)
            return
        if method == "dpad_steps":
            self.writer.dpad("L", int(self.config.get("colour_rect_width", 212)))
            self.writer.dpad("U", int(self.config.get("colour_rect_height", 111)))
            self.writer.wait(settle_frames)
            return
        raise ValueError(
            "anchor_colour_rect_method must be 'analog', 'dpad_hold', or 'dpad_steps'"
        )

    def _anchor_colour_rect_bottom_left(self) -> None:
        method = str(self.config.get("anchor_colour_rect_method", "analog"))
        hold_frames = int(self.timing.get("colour_rect_anchor_hold_frames", 45))
        settle_frames = int(self.timing.get("colour_rect_anchor_settle_frames", 4))
        neutral = int(self.config.get("stick", {}).get("neutral", 128))
        stick_min = int(self.config.get("stick", {}).get("min", 0))
        stick_max = int(self.config.get("stick", {}).get("max", 255))

        if method == "analog":
            self.writer.stick(stick_min, stick_max, neutral, neutral, hold_frames)
            self.writer.stick(neutral, neutral, neutral, neutral, settle_frames)
            return
        if method == "dpad_hold":
            self.writer.hold(["L", "D"], hold_frames)
            self.writer.release(settle_frames)
            return
        if method == "dpad_steps":
            self.writer.dpad("L", int(self.config.get("colour_rect_width", 212)))
            self.writer.dpad("D", int(self.config.get("colour_rect_height", 111)))
            self.writer.wait(settle_frames)
            return
        raise ValueError(
            "anchor_colour_rect_method must be 'analog', 'dpad_hold', or 'dpad_steps'"
        )

    def _validate_slot(self, slot_index: int) -> None:
        if slot_index < 0 or slot_index >= self.palette_slots:
            raise ValueError(f"slot_index must be in range 0..{self.palette_slots - 1}")
