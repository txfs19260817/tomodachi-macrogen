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
