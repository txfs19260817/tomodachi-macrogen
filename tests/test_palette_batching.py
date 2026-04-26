import unittest

from src.palette import PaletteColor, make_batches, rgb_to_hsv


class TestPaletteBatching(unittest.TestCase):
    def test_batches_split_over_palette_slots(self) -> None:
        colors = [
            PaletteColor(
                color_index=index,
                rgb=(index, index, index),
                hsv=rgb_to_hsv((index, index, index)),
                pixel_count=10 - index,
            )
            for index in range(10)
        ]

        batches = make_batches(colors, 9)

        self.assertEqual(len(batches), 2)
        self.assertEqual(len(batches[0]), 9)
        self.assertEqual(len(batches[1]), 1)
        self.assertEqual(batches[0][0].assigned_slot, 0)
        self.assertEqual(batches[1][0].assigned_slot, 0)


if __name__ == "__main__":
    unittest.main()
