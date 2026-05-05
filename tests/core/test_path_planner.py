import unittest

from src.core.path_planner import (
    PATH_STRATEGIES,
    PathPlanningStrategy,
    get_path_strategy,
    iter_path_strategies,
    plan_color_pixels,
)


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

    def test_snake_strategy_sweeps_rows_from_nearest_endpoint(self) -> None:
        indices = [
            [1, 0, 1, 1],
            [1, 1, 0, 1],
        ]

        self.assertEqual(
            plan_color_pixels(indices, 1, strategy="snake"),
            [(0, 0), (2, 0), (3, 0), (3, 1), (1, 1), (0, 1)],
        )

    def test_tsp_strategy_uses_two_opt_over_horizontal_runs(self) -> None:
        indices = [
            [0, 1, 0, 1],
            [1, 1, 0, 0],
        ]

        self.assertEqual(
            plan_color_pixels(indices, 1, strategy="tsp"),
            [(0, 1), (1, 1), (1, 0), (3, 0)],
        )

    def test_strategies_are_registered_objects(self) -> None:
        strategies = iter_path_strategies()

        self.assertEqual(PATH_STRATEGIES, ("nearest-runs", "snake", "tsp"))
        self.assertTrue(all(isinstance(strategy, PathPlanningStrategy) for strategy in strategies))
        self.assertIs(get_path_strategy("tsp"), strategies[2])

    def test_missing_color_returns_empty_path(self) -> None:
        self.assertEqual(plan_color_pixels([[0, None], [0, 0]], 1), [])


if __name__ == "__main__":
    unittest.main()
