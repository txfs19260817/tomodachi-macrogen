import tempfile
import unittest
from pathlib import Path

from swicc_runner import (
    MATCH_CONTROLLER_SETTLE_FRAMES,
    MacroCommand,
    build_command_list,
    convert_button_string,
    encode_macro_command,
    expand_macro_paths,
    parse_macro_line,
)


class TestSwiccRunner(unittest.TestCase):
    def test_parse_macro_line_with_buttons_sticks_and_comment(self) -> None:
        command = parse_macro_line("{ZL A} (0 255 128 128) 9 ; comment")

        self.assertEqual(
            command,
            MacroCommand(buttons="L2 A", frames=9, lx=0, ly=255, rx=128, ry=128),
        )

    def test_convert_button_string_matches_glams_mapping(self) -> None:
        self.assertEqual(convert_button_string("A L1 R2 U R"), (0, 148, 1))

    def test_encode_macro_command_matches_swicc_q_format(self) -> None:
        self.assertEqual(
            encode_macro_command(MacroCommand(buttons="A", frames=2)),
            "+Q 00040880808080\n",
        )

    def test_expand_macro_paths_uses_natural_filename_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ["color_10.txt", "color_02.txt", "color_01.txt"]:
                (root / name).write_text("{A} 1\n", encoding="utf-8")

            paths = expand_macro_paths([str(root / "color_*.txt")])

            self.assertEqual(
                [path.name for path in paths],
                ["color_01.txt", "color_02.txt", "color_10.txt"],
            )

    def test_match_controller_waits_before_file_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            macro = Path(tmp) / "color_01.txt"
            macro.write_text("{A} 1\n", encoding="utf-8")

            commands = build_command_list([macro], match_controller=True)

            self.assertEqual(
                commands[-2],
                MacroCommand(
                    buttons="",
                    frames=MATCH_CONTROLLER_SETTLE_FRAMES,
                    source="controller-match-settle",
                ),
            )
            self.assertEqual(commands[-1].buttons, "A")

    def test_match_controller_only_does_not_add_settle_wait(self) -> None:
        commands = build_command_list([], match_controller=True)

        self.assertFalse(
            any(command.source == "controller-match-settle" for command in commands)
        )


if __name__ == "__main__":
    unittest.main()
