from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, Literal

type Point = tuple[int, int]
type Run = tuple[int, int, int]
type OrientedRun = tuple[Run, bool]
type PathStrategy = Literal["nearest-runs", "snake", "tsp"]

DEFAULT_TSP_MAX_RUNS = 400
TSP_2OPT_MAX_PASSES = 4


@dataclass(frozen=True)
class PathPlanningContext:
    indices: Sequence[Sequence[int | None]]
    color_index: int
    start: Point = (0, 0)
    diagonal_movement: bool = False
    tsp_max_runs: int = DEFAULT_TSP_MAX_RUNS


class PathPlanningStrategy(ABC):
    name: ClassVar[PathStrategy]

    @abstractmethod
    def plan(self, context: PathPlanningContext) -> list[Point]:
        raise NotImplementedError


class NearestRunsStrategy(PathPlanningStrategy):
    name = "nearest-runs"

    def plan(self, context: PathPlanningContext) -> list[Point]:
        runs = _horizontal_run_units(context.indices, context.color_index)
        ordered = _nearest_oriented_runs(
            runs,
            context.start,
            diagonal_movement=context.diagonal_movement,
        )
        return _oriented_run_points(ordered)


class SnakeRowsStrategy(PathPlanningStrategy):
    name = "snake"

    def plan(self, context: PathPlanningContext) -> list[Point]:
        runs = _horizontal_run_units(context.indices, context.color_index)
        if not runs:
            return []

        runs_by_y: dict[int, list[Run]] = {}
        for run in runs:
            runs_by_y.setdefault(run[0], []).append(run)

        current = context.start
        ordered: list[OrientedRun] = []
        for y in sorted(runs_by_y):
            row_runs = sorted(runs_by_y[y], key=lambda run: run[1])
            forward_start = (row_runs[0][1], y)
            reverse_start = (row_runs[-1][2], y)
            reverse = _travel_distance(
                current,
                reverse_start,
                diagonal_movement=context.diagonal_movement,
            ) < _travel_distance(
                current,
                forward_start,
                diagonal_movement=context.diagonal_movement,
            )
            selected_runs = reversed(row_runs) if reverse else row_runs
            for run in selected_runs:
                ordered.append((run, reverse))
            first_run = row_runs[0]
            last_run = row_runs[-1]
            current = (first_run[1], y) if reverse else (last_run[2], y)
        return _oriented_run_points(ordered)


class TspRunsStrategy(PathPlanningStrategy):
    name = "tsp"

    def plan(self, context: PathPlanningContext) -> list[Point]:
        runs = _horizontal_run_units(context.indices, context.color_index)
        ordered = _nearest_oriented_runs(
            runs,
            context.start,
            diagonal_movement=context.diagonal_movement,
        )
        max_runs = max(0, context.tsp_max_runs)
        if len(ordered) > max_runs:
            return _oriented_run_points(ordered)
        optimized = _two_opt_oriented_runs(
            ordered,
            context.start,
            diagonal_movement=context.diagonal_movement,
        )
        return _oriented_run_points(optimized)


PATH_PLANNING_STRATEGIES: tuple[PathPlanningStrategy, ...] = (
    NearestRunsStrategy(),
    SnakeRowsStrategy(),
    TspRunsStrategy(),
)
PATH_STRATEGIES: tuple[PathStrategy, ...] = tuple(
    strategy.name for strategy in PATH_PLANNING_STRATEGIES
)


def iter_path_strategies() -> tuple[PathPlanningStrategy, ...]:
    return PATH_PLANNING_STRATEGIES


def get_path_strategy(name: PathStrategy | str) -> PathPlanningStrategy:
    for strategy in PATH_PLANNING_STRATEGIES:
        if strategy.name == name:
            return strategy
    raise ValueError(f"unsupported path strategy: {name}")


def plan_color_pixels(
    indices: Sequence[Sequence[int | None]],
    color_index: int,
    *,
    start: Point = (0, 0),
    strategy: PathStrategy | str = "nearest-runs",
    diagonal_movement: bool = False,
    tsp_max_runs: int = DEFAULT_TSP_MAX_RUNS,
) -> list[Point]:
    context = PathPlanningContext(
        indices=indices,
        color_index=color_index,
        start=start,
        diagonal_movement=diagonal_movement,
        tsp_max_runs=tsp_max_runs,
    )
    return get_path_strategy(strategy).plan(context)


def _nearest_oriented_runs(
    runs: Sequence[Run],
    start: Point,
    *,
    diagonal_movement: bool,
) -> list[OrientedRun]:
    remaining = set(runs)
    current = start
    ordered: list[OrientedRun] = []
    while remaining:
        run, reverse, _key = min(
            (_run_choice(run, current, diagonal_movement=diagonal_movement) for run in remaining),
            key=lambda choice: choice[2],
        )
        remaining.remove(run)
        ordered.append((run, reverse))
        current = _oriented_run_end((run, reverse))
    return ordered


def _two_opt_oriented_runs(
    ordered: list[OrientedRun],
    start: Point,
    *,
    diagonal_movement: bool,
) -> list[OrientedRun]:
    if len(ordered) < 3:
        return ordered

    optimized = list(ordered)
    for _pass in range(TSP_2OPT_MAX_PASSES):
        improved = False
        for i in range(len(optimized) - 1):
            previous_end = start if i == 0 else _oriented_run_end(optimized[i - 1])
            for j in range(i + 1, len(optimized)):
                next_start = (
                    _oriented_run_start(optimized[j + 1])
                    if j + 1 < len(optimized)
                    else None
                )
                old_cost = _edge_cost(
                    previous_end,
                    _oriented_run_start(optimized[i]),
                    diagonal_movement=diagonal_movement,
                )
                new_cost = _edge_cost(
                    previous_end,
                    _oriented_run_end(optimized[j]),
                    diagonal_movement=diagonal_movement,
                )
                if next_start is not None:
                    old_cost += _edge_cost(
                        _oriented_run_end(optimized[j]),
                        next_start,
                        diagonal_movement=diagonal_movement,
                    )
                    new_cost += _edge_cost(
                        _oriented_run_start(optimized[i]),
                        next_start,
                        diagonal_movement=diagonal_movement,
                    )
                if new_cost < old_cost:
                    optimized[i : j + 1] = [
                        _flip_oriented_run(run) for run in reversed(optimized[i : j + 1])
                    ]
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return optimized


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


def _run_choice(
    run: Run,
    current: Point,
    *,
    diagonal_movement: bool,
) -> tuple[Run, bool, tuple[int, int, int, int]]:
    forward_start = _run_start(run, reverse=False)
    reverse_start = _run_start(run, reverse=True)
    forward_distance = _travel_distance(
        current,
        forward_start,
        diagonal_movement=diagonal_movement,
    )
    reverse_distance = _travel_distance(
        current,
        reverse_start,
        diagonal_movement=diagonal_movement,
    )
    reverse = reverse_distance < forward_distance
    distance = reverse_distance if reverse else forward_distance
    first_x = reverse_start[0] if reverse else forward_start[0]
    y, x_start, _x_end = run
    return run, reverse, (distance, y, first_x, x_start)


def _oriented_run_points(runs: Sequence[OrientedRun]) -> list[Point]:
    ordered: list[Point] = []
    for run, reverse in runs:
        ordered.extend(_run_points(run, reverse=reverse))
    return ordered


def _run_points(run: Run, *, reverse: bool) -> list[Point]:
    y, x_start, x_end = run
    x_values = range(x_end, x_start - 1, -1) if reverse else range(x_start, x_end + 1)
    return [(x, y) for x in x_values]


def _oriented_run_start(run: OrientedRun) -> Point:
    raw_run, reverse = run
    return _run_start(raw_run, reverse=reverse)


def _oriented_run_end(run: OrientedRun) -> Point:
    raw_run, reverse = run
    return _run_end(raw_run, reverse=reverse)


def _run_start(run: Run, *, reverse: bool) -> Point:
    y, x_start, x_end = run
    return (x_end if reverse else x_start, y)


def _run_end(run: Run, *, reverse: bool) -> Point:
    y, x_start, x_end = run
    return (x_start if reverse else x_end, y)


def _flip_oriented_run(run: OrientedRun) -> OrientedRun:
    raw_run, reverse = run
    return raw_run, not reverse


def _edge_cost(a: Point, b: Point, *, diagonal_movement: bool) -> int:
    return _travel_distance(a, b, diagonal_movement=diagonal_movement)


def _travel_distance(a: Point, b: Point, *, diagonal_movement: bool) -> int:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    if diagonal_movement:
        return max(dx, dy)
    return dx + dy
