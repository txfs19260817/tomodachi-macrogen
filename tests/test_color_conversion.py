import unittest

from src.palette import rgb_to_hsv


class TestColorConversion(unittest.TestCase):
    def test_red_rgb_to_hsv(self) -> None:
        hue, saturation, value = rgb_to_hsv((255, 0, 0))
        self.assertAlmostEqual(hue, 0.0)
        self.assertAlmostEqual(saturation, 1.0)
        self.assertAlmostEqual(value, 1.0)

    def test_black_rgb_to_hsv(self) -> None:
        hue, saturation, value = rgb_to_hsv((0, 0, 0))
        self.assertAlmostEqual(hue, 0.0)
        self.assertAlmostEqual(saturation, 0.0)
        self.assertAlmostEqual(value, 0.0)


if __name__ == "__main__":
    unittest.main()
