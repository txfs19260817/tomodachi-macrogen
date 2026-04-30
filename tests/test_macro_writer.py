import unittest

from src.macro_writer import MacroWriter


class TestMacroWriter(unittest.TestCase):
    def test_tap_outputs_hold_and_release(self) -> None:
        writer = MacroWriter({"timing": {"tap_hold_frames": 2, "tap_release_frames": 1}})
        writer.tap("A")
        self.assertEqual([line.text for line in writer.lines], ["{A} 2", "{} 1"])

    def test_button_aliases_map_to_glams_names(self) -> None:
        writer = MacroWriter()
        writer.tap("zr", 3, 2)
        self.assertEqual([line.text for line in writer.lines], ["{R2} 3", "{} 2"])

    def test_stick_can_hold_buttons_at_the_same_time(self) -> None:
        writer = MacroWriter()
        writer.stick(0, 255, 128, 128, 9, buttons="ZL")
        self.assertEqual([line.text for line in writer.lines], ["{L2} (0 255 128 128) 9"])

    def test_dpad_does_not_track_canvas_position(self) -> None:
        writer = MacroWriter()
        writer.dpad("R", 3)
        self.assertEqual((writer.current_x, writer.current_y), (0, 0))

    def test_move_cursor_tracks_canvas_position(self) -> None:
        writer = MacroWriter(
            {
                "timing": {
                    "movement_hold_frames": 1,
                    "movement_release_frames": 1,
                }
            }
        )
        writer.move_cursor_to(2, 1)
        self.assertEqual((writer.current_x, writer.current_y), (2, 1))
        self.assertEqual(
            [line.text for line in writer.lines],
            ["{R} 1", "{} 1", "{R} 1", "{} 1", "{D} 1", "{} 1"],
        )

    def test_move_cursor_can_pause_between_movement_chunks(self) -> None:
        writer = MacroWriter(
            {
                "timing": {
                    "movement_hold_frames": 1,
                    "movement_release_frames": 1,
                    "movement_chunk_size": 2,
                    "movement_chunk_settle_frames": 5,
                }
            }
        )
        writer.move_cursor_to(5, 0)
        self.assertEqual(
            [line.text for line in writer.lines],
            [
                "{R} 1",
                "{} 1",
                "{R} 1",
                "{} 1",
                "{} 5",
                "{R} 1",
                "{} 1",
                "{R} 1",
                "{} 1",
                "{} 5",
                "{R} 1",
                "{} 1",
            ],
        )

    def test_draw_pixels_drags_adjacent_horizontal_run(self) -> None:
        writer = MacroWriter(
            {
                "timing": {
                    "draw_hold_frames": 3,
                    "draw_release_frames": 2,
                    "movement_hold_frames": 1,
                    "movement_release_frames": 1,
                }
            }
        )

        writer.draw_pixels([(0, 0), (1, 0), (2, 0)])

        self.assertEqual(writer.draw_events, [(0, 0), (1, 0), (2, 0)])
        self.assertEqual(writer.canvas_position(), (2, 0))
        self.assertEqual(
            [line.text for line in writer.lines],
            [
                "{A} 3",
                "{A R} 1",
                "{A} 1",
                "{A R} 1",
                "{A} 1",
                "{} 2",
            ],
        )

    def test_draw_pixels_splits_non_adjacent_runs(self) -> None:
        writer = MacroWriter(
            {
                "timing": {
                    "draw_hold_frames": 3,
                    "draw_release_frames": 2,
                    "movement_hold_frames": 1,
                    "movement_release_frames": 1,
                }
            }
        )

        writer.draw_pixels([(0, 0), (1, 0), (3, 0)])

        self.assertEqual(writer.draw_events, [(0, 0), (1, 0), (3, 0)])
        self.assertEqual(writer.canvas_position(), (3, 0))
        self.assertEqual(
            [line.text for line in writer.lines],
            [
                "{A} 3",
                "{A R} 1",
                "{A} 1",
                "{} 2",
                "{R} 1",
                "{} 1",
                "{R} 1",
                "{} 1",
                "{A} 3",
                "{} 2",
            ],
        )

    def test_draw_pixels_drags_reverse_horizontal_run(self) -> None:
        writer = MacroWriter(
            {
                "timing": {
                    "draw_hold_frames": 3,
                    "draw_release_frames": 2,
                    "movement_hold_frames": 1,
                    "movement_release_frames": 1,
                }
            }
        )
        writer.current_x = 2

        writer.draw_pixels([(2, 0), (1, 0), (0, 0)])

        self.assertEqual(writer.draw_events, [(2, 0), (1, 0), (0, 0)])
        self.assertEqual(writer.canvas_position(), (0, 0))
        self.assertEqual(
            [line.text for line in writer.lines],
            [
                "{A} 3",
                "{A L} 1",
                "{A} 1",
                "{A L} 1",
                "{A} 1",
                "{} 2",
            ],
        )

    def test_reset_canvas_to_origin_uses_fixed_physical_anchor(self) -> None:
        writer = MacroWriter(
            {
                "canvas_reset_right_steps": 2,
                "canvas_reset_down_steps": 1,
                "timing": {
                    "canvas_reset_hold_frames": 3,
                    "canvas_reset_settle_frames": 2,
                    "movement_hold_frames": 1,
                    "movement_release_frames": 1,
                },
            }
        )
        writer.current_x = 12
        writer.current_y = 34

        writer.reset_canvas_to_origin()

        self.assertEqual(writer.canvas_position(), (0, 0))
        self.assertEqual(
            [line.text for line in writer.lines],
            [
                "{} (0 0 128 128) 3",
                "{} (128 128 128 128) 2",
                "{R} 1",
                "{} 1",
                "{R} 1",
                "{} 1",
                "{D} 1",
                "{} 1",
            ],
        )

    def test_split_lines_zero_disables_splitting(self) -> None:
        writer = MacroWriter()
        writer.tap("A")
        writer.tap("B")

        self.assertEqual(
            writer.split_output(0),
            [["{A} 2", "{} 1", "{B} 2", "{} 1"]],
        )


if __name__ == "__main__":
    unittest.main()
