import unittest

from src.color_picker import ColorPicker
from src.living_grid import GamePaletteTarget, PressCounts
from src.macro_writer import MacroWriter


class TestColorPickerPress(unittest.TestCase):
    def test_press_counts_use_r2_right_and_up(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "dpad_steps",
            "colour_rect_width": 10,
            "colour_rect_height": 10,
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

    def test_picker_default_reset_holds_zl_with_lower_left_stick(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "analog",
            "timing": {
                "colour_rect_anchor_hold_frames": 9,
                "colour_rect_anchor_settle_frames": 1,
                "colour_rect_step_hold_frames": 1,
                "colour_rect_step_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.reset_picker_to_default()

        self.assertEqual(
            [line.text for line in writer.lines],
            ["{L2} (0 255 128 128) 9", "{} (128 128 128 128) 1"],
        )

    def test_right_side_saturation_anchors_right_then_moves_left(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "analog",
            "colour_rect_width": 212,
            "colour_rect_height": 111,
            "timing": {
                "colour_rect_anchor_hold_frames": 9,
                "colour_rect_anchor_settle_frames": 1,
                "colour_rect_step_hold_frames": 1,
                "colour_rect_step_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.reset_picker_to_default()
        picker._move_colour_rect_to_press_count(208, 2)

        lines = [line.text for line in writer.lines]
        self.assertIn("{} (255 255 128 128) 9", lines)
        self.assertEqual(lines.count("{L} 1"), 3)
        self.assertEqual(lines.count("{U} 1"), 2)
        self.assertNotIn("{R2} 1", lines)

    def test_right_side_hue_anchors_right_then_moves_left(self) -> None:
        config = {
            "hue_slider_steps": 202,
            "timing": {
                "hue_anchor_hold_frames": 9,
                "hue_anchor_release_frames": 1,
                "hue_step_hold_frames": 1,
                "hue_step_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker._move_hue_to_press_count(198)

        lines = [line.text for line in writer.lines]
        self.assertEqual(lines[:2], ["{R2} 9", "{} 1"])
        self.assertEqual(lines.count("{L2} 1"), 3)
        self.assertNotIn("{R2} 1", lines)

    def test_top_side_brightness_anchors_top_then_moves_down(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "analog",
            "colour_rect_width": 212,
            "colour_rect_height": 111,
            "timing": {
                "colour_rect_anchor_hold_frames": 9,
                "colour_rect_anchor_settle_frames": 1,
                "colour_rect_step_hold_frames": 1,
                "colour_rect_step_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.reset_picker_to_default()
        picker._move_colour_rect_to_press_count(2, 108)

        lines = [line.text for line in writer.lines]
        self.assertIn("{} (0 0 128 128) 9", lines)
        self.assertEqual(lines.count("{R} 1"), 2)
        self.assertEqual(lines.count("{D} 1"), 2)
        self.assertNotIn("{U} 1", lines)

    def test_top_right_colour_rect_anchors_top_right(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "analog",
            "colour_rect_width": 212,
            "colour_rect_height": 111,
            "timing": {
                "colour_rect_anchor_hold_frames": 9,
                "colour_rect_anchor_settle_frames": 1,
                "colour_rect_step_hold_frames": 1,
                "colour_rect_step_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.reset_picker_to_default()
        picker._move_colour_rect_to_press_count(208, 108)

        lines = [line.text for line in writer.lines]
        self.assertIn("{} (255 0 128 128) 9", lines)
        self.assertEqual(lines.count("{L} 1"), 3)
        self.assertEqual(lines.count("{D} 1"), 2)

    def test_current_slot_press_resets_before_setting_hue(self) -> None:
        config = {
            "palette_slots": 9,
            "anchor_colour_rect_method": "analog",
            "timing": {
                "tap_hold_frames": 1,
                "tap_release_frames": 1,
                "menu_open_frames": 1,
                "screen_settle_frames": 1,
                "menu_close_frames": 1,
                "colour_rect_anchor_hold_frames": 9,
                "colour_rect_anchor_settle_frames": 1,
                "hue_step_hold_frames": 1,
                "hue_step_release_frames": 1,
                "colour_rect_step_hold_frames": 1,
                "colour_rect_step_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.set_current_palette_slot_press(PressCounts(h=2, s=0, b=0))

        lines = [line.text for line in writer.lines]
        reset_index = lines.index("{L2} (0 255 128 128) 9")
        hue_index = lines.index("{R2} 1")
        self.assertLess(reset_index, hue_index)

    def test_current_slot_game_palette_uses_default_palette_without_r_tab(self) -> None:
        config = {
            "game_palette_cols": 11,
            "timing": {
                "tap_hold_frames": 1,
                "tap_release_frames": 1,
                "menu_open_frames": 1,
                "screen_settle_frames": 1,
                "menu_close_frames": 1,
                "game_palette_anchor_hold_frames": 3,
                "game_palette_anchor_settle_frames": 2,
                "movement_hold_frames": 1,
                "movement_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.set_current_palette_slot_game(GamePaletteTarget(kind="grid", row=2, col=3))

        lines = [line.text for line in writer.lines]
        self.assertNotIn("{R1} 1", lines)
        self.assertIn("{L U} 3", lines)
        self.assertEqual(lines.count("{R} 1"), 2)
        self.assertEqual(lines.count("{D} 1"), 1)

    def test_current_slot_game_palette_extra_uses_side_strip_column(self) -> None:
        config = {
            "game_palette_cols": 11,
            "timing": {
                "tap_hold_frames": 1,
                "tap_release_frames": 1,
                "menu_open_frames": 1,
                "screen_settle_frames": 1,
                "menu_close_frames": 1,
                "game_palette_anchor_hold_frames": 3,
                "game_palette_anchor_settle_frames": 2,
                "movement_hold_frames": 1,
                "movement_release_frames": 1,
            },
        }
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)

        picker.set_current_palette_slot_game(GamePaletteTarget(kind="extra", row=2))

        lines = [line.text for line in writer.lines]
        self.assertEqual(lines.count("{R} 1"), 11)
        self.assertEqual(lines.count("{D} 1"), 1)


if __name__ == "__main__":
    unittest.main()
