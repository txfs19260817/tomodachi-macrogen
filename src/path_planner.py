from collections.abc import Sequence

type Point = tuple[int, int]
type Run = tuple[int, int, int]


def plan_color_pixels(
    indices: Sequence[Sequence[int | None]],
    color_index: int,
    *,
    start: Point = (0, 0),
) -> list[Point]:
    runs = _horizontal_run_units(indices, color_index)
    if not runs:
        return []

    remaining = set(runs)
    current = start
    ordered: list[Point] = []
    while remaining:
        run, reverse, _key = min(
            (_run_choice(run, current) for run in remaining),
            key=lambda choice: choice[2],
        )
        remaining.remove(run)
        ordered.extend(_run_points(run, reverse=reverse))
        y, x_start, x_end = run
        current = (x_start if reverse else x_end, y)
    return ordered


def _horizontal_run_units(
    indices: Sequence[Sequence[int | None]],
    color_index: int,
) -> list[Run]:
    runs: list[Run] = []
    for y, row in enumerate(indices):
        x = 0
        while x < len(row):
            if row[x] != color_index:
                x += 1
                continue
            x_start = x
            while x < len(row) and row[x] == color_index:
                x += 1
            runs.append((y, x_start, x - 1))
    return runs


def _run_choice(run: Run, current: Point) -> tuple[Run, bool, tuple[int, int, int, int]]:
    y, x_start, x_end = run
    forward_distance = _manhattan(current, (x_start, y))
    reverse_distance = _manhattan(current, (x_end, y))
    reverse = reverse_distance < forward_distance
    distance = reverse_distance if reverse else forward_distance
    first_x = x_end if reverse else x_start
    return run, reverse, (distance, y, first_x, x_start)


def _run_points(run: Run, *, reverse: bool) -> list[Point]:
    y, x_start, x_end = run
    x_values = range(x_end, x_start - 1, -1) if reverse else range(x_start, x_end + 1)
    return [(x, y) for x in x_values]


def _manhattan(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
