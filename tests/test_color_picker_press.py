import unittest

from src.color_picker import ColorPicker
from src.living_grid import PressCounts
from src.macro_writer import MacroWriter


class TestColorPickerPress(unittest.TestCase):
    def test_press_counts_use_r2_right_and_up(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "dpad_steps",
            "colour_rect_width": 0,
            "colour_rect_height": 0,
            "timing": {
                "tap_hold_frames": 1,
                "tap_release_frames": 1,
                "hue_anchor_hold_frames": 1,
                "hue_anchor_release_frames": 1,
                "hue_step_hold_frames": 1,
                "hue_step_release_frames": 1,
                "colour_rect_step_hold_frames": 1,
                "colour_rect_step_release_frames": 1,
                "colour_rect_anchor_settle_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.set_hue_press_count(2)
        picker.set_colour_rect_press_count(3, 4)

        lines = [line.text for line in writer.lines]
        self.assertEqual(lines.count("{R2} 1"), 2)
        self.assertEqual(lines.count("{R} 1"), 3)
        self.assertEqual(lines.count("{U} 1"), 4)

    def test_current_slot_press_uses_two_y_presses_without_slot_navigation(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "dpad_steps",
            "colour_rect_width": 0,
            "colour_rect_height": 0,
            "timing": {
                "tap_hold_frames": 1,
                "tap_release_frames": 1,
                "menu_open_frames": 1,
                "screen_settle_frames": 1,
                "menu_close_frames": 1,
                "slot_anchor_hold_frames": 99,
                "hue_anchor_hold_frames": 1,
                "hue_anchor_release_frames": 1,
                "hue_step_hold_frames": 1,
                "hue_step_release_frames": 1,
                "colour_rect_step_hold_frames": 1,
                "colour_rect_step_release_frames": 1,
                "colour_rect_anchor_settle_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.set_current_palette_slot_press(PressCounts(h=0, s=0, b=0))

        lines = [line.text for line in writer.lines]
        self.assertEqual(lines[:6], ["{Y} 1", "{} 1", "{} 1", "{Y} 1", "{} 1", "{} 1"])
        self.assertNotIn("{D} 99", lines)


if __name__ == "__main__":
    unittest.main()
