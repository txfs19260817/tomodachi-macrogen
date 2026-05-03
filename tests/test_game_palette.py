import unittest

from src.game_palette import find_game_palette_target


class TestGamePalette(unittest.TestCase):
    def test_finds_main_grid_coordinates_from_84_color_layout(self) -> None:
        cases = {
            "#FFFFFF": ("grid", 1, 1),
            "#F0F0F8": ("grid", 1, 3),
            "#06C2FE": ("grid", 4, 4),
            "#EBEBEB": ("grid", 2, 1),
            "#34220D": ("grid", 7, 11),
        }

        for hex_value, expected in cases.items():
            with self.subTest(hex_value=hex_value):
                rgb = _hex_to_rgb(hex_value)
                self.assertEqual(find_game_palette_target(hex_value, rgb), expected)

    def test_finds_extra_strip_coordinates_from_84_color_layout(self) -> None:
        self.assertEqual(find_game_palette_target("#FE2500", (254, 37, 0)), ("extra", 1, None))
        self.assertEqual(find_game_palette_target("#FF36C3", (255, 54, 195)), ("extra", 7, None))


def _hex_to_rgb(hex_value: str) -> tuple[int, int, int]:
    return (
        int(hex_value[1:3], 16),
        int(hex_value[3:5], 16),
        int(hex_value[5:7], 16),
    )


if __name__ == "__main__":
    unittest.main()
