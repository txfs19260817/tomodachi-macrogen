from collections.abc import Sequence
from typing import Literal

type Point = tuple[int, int]
type PathMode = Literal["safe-pixel", "nearest", "horizontal-runs"]


def plan_color_pixels(
    indices: Sequence[Sequence[int | None]],
    color_index: int,
    *,
    mode: PathMode = "safe-pixel",
) -> list[Point]:
    if mode == "safe-pixel":
        return snake_scan(indices, color_index)
    if mode == "nearest":
        return nearest_neighbor(snake_scan(indices, color_index))
    if mode == "horizontal-runs":
        return horizontal_runs(indices, color_index)
    raise ValueError("mode must be safe-pixel, nearest, or horizontal-runs")


def snake_scan(indices: Sequence[Sequence[int | None]], color_index: int) -> list[Point]:
    points: list[Point] = []
    for y, row in enumerate(indices):
        width = len(row)
        x_values = range(width) if y % 2 == 0 else range(width - 1, -1, -1)
        for x in x_values:
            if row[x] == color_index:
                points.append((x, y))
    return points


def horizontal_runs(indices: Sequence[Sequence[int | None]], color_index: int) -> list[Point]:
    points: list[Point] = []
    for y, row in enumerate(indices):
        width = len(row)
        if y % 2 == 0:
            x = 0
            while x < width:
                if row[x] != color_index:
                    x += 1
                    continue
                while x < width and row[x] == color_index:
                    points.append((x, y))
                    x += 1
        else:
            x = width - 1
            while x >= 0:
                if row[x] != color_index:
                    x -= 1
                    continue
                while x >= 0 and row[x] == color_index:
                    points.append((x, y))
                    x -= 1
    return points


def nearest_neighbor(points: list[Point]) -> list[Point]:
    if len(points) <= 1:
        return points[:]
    if len(points) > 4096:
        return points[:]

    remaining = set(points)
    current = (0, 0)
    ordered: list[Point] = []
    while remaining:
        next_point = min(
            remaining,
            key=lambda point: (
                abs(point[0] - current[0]) + abs(point[1] - current[1]),
                point[1],
                point[0],
            ),
        )
        ordered.append(next_point)
        remaining.remove(next_point)
        current = next_point
    return ordered
