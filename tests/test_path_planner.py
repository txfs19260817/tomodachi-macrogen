import unittest

from src.path_planner import horizontal_runs, nearest_neighbor, snake_scan


class TestPathPlanner(unittest.TestCase):
    def test_snake_scan(self) -> None:
        indices = [
            [1, 0, 1],
            [1, 1, 0],
        ]
        self.assertEqual(snake_scan(indices, 1), [(0, 0), (2, 0), (1, 1), (0, 1)])

    def test_horizontal_runs_preserve_snake_direction(self) -> None:
        indices = [
            [1, 1, 0],
            [0, 1, 1],
        ]
        self.assertEqual(horizontal_runs(indices, 1), [(0, 0), (1, 0), (2, 1), (1, 1)])

    def test_nearest_neighbor_starts_from_origin(self) -> None:
        points = [(5, 5), (1, 0), (2, 0)]
        self.assertEqual(nearest_neighbor(points), [(1, 0), (2, 0), (5, 5)])


if __name__ == "__main__":
    unittest.main()
