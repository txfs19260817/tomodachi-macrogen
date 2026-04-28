import unittest

from src.path_planner import plan_color_pixels


class TestPathPlanner(unittest.TestCase):
    def test_uses_nearest_horizontal_run_endpoint(self) -> None:
        indices = [
            [1, 1, 0, 0, 1, 1],
            [0, 0, 0, 0, 0, 0],
        ]

        self.assertEqual(
            plan_color_pixels(indices, 1, start=(5, 0)),
            [(5, 0), (4, 0), (1, 0), (0, 0)],
        )

    def test_preserves_same_pixel_set(self) -> None:
        indices = [
            [1, 0, 1, 1],
            [0, 1, 0, 1],
            [1, 1, 0, None],
        ]
        expected = {
            (x, y)
            for y, row in enumerate(indices)
            for x, value in enumerate(row)
            if value == 1
        }

        self.assertEqual(set(plan_color_pixels(indices, 1)), expected)

    def test_missing_color_returns_empty_path(self) -> None:
        self.assertEqual(plan_color_pixels([[0, None], [0, 0]], 1), [])


if __name__ == "__main__":
    unittest.main()
