from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

from src.core.config import AppConfig
from src.core.living_grid import LivingGridData, load_living_grid_json
from src.core.palette import PaletteColor
from src.core.path_planner import PathPlanningContext, PathPlanningStrategy, iter_path_strategies
from src.macro.timing import dry_run_draw
from tomodachi_macrogen import build_living_grid_colors, choose_color_path, load_config

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

FIXTURES = {
    "full-hsb": FIXTURE_ROOT / "example.json",
    "game": FIXTURE_ROOT / "example_game.json",
    "full84": FIXTURE_ROOT / "example_full84.json",
}


@dataclass(frozen=True)
class FixtureCase:
    name: str
    grid: LivingGridData
    colors: list[PaletteColor]
    config: AppConfig


@dataclass(frozen=True)
class PlanningSummary:
    total_frames: int
    saved_frames: int
    strategy_counts: dict[str, int]


def load_fixture_cases() -> dict[str, FixtureCase]:
    return {name: _load_fixture_case(name, path) for name, path in FIXTURES.items()}


def planner_strategy_names() -> tuple[str, ...]:
    return tuple(strategy.name for strategy in iter_path_strategies())


def _load_fixture_case(name: str, path: Path) -> FixtureCase:
    grid = load_living_grid_json(path)
    config = load_config(None)
    if config.canvas_cell_step is None:
        config = config.with_canvas_cell_step(grid.brush_px)
    colors = build_living_grid_colors(grid, config.color_order)
    return FixtureCase(name=name, grid=grid, colors=colors, config=config)


def benchmark_single_strategy(
    case: FixtureCase,
    strategy: PathPlanningStrategy,
    *,
    tsp_max_runs: int,
) -> PlanningSummary:
    total_frames = 0
    for color in case.colors:
        context = PathPlanningContext(
            indices=case.grid.indices,
            color_index=color.color_index,
            start=(0, 0),
            diagonal_movement=case.config.enable_diagonal_movement,
            tsp_max_runs=tsp_max_runs,
        )
        points = strategy.plan(context)
        total_frames += dry_run_draw(case.config, points, start=(0, 0)).frame_count
    return PlanningSummary(
        total_frames=total_frames,
        saved_frames=0,
        strategy_counts={strategy.name: len(case.colors)},
    )


def benchmark_auto_tsp_limit(case: FixtureCase, *, tsp_max_runs: int) -> PlanningSummary:
    config = replace(case.config, path_tsp_max_runs=tsp_max_runs)
    total_frames = 0
    saved_frames = 0
    strategy_counts: Counter[str] = Counter()
    for color in case.colors:
        chosen = choose_color_path(
            config,
            case.grid.indices,
            color.color_index,
            start=(0, 0),
        )
        total_frames += chosen.draw_frame_count
        strategy_counts[chosen.strategy] += 1
        baseline = chosen.path_candidate_frames.get("nearest-runs")
        if baseline is not None and chosen.path_candidate_frames:
            saved_frames += baseline - min(chosen.path_candidate_frames.values())
    return PlanningSummary(
        total_frames=total_frames,
        saved_frames=saved_frames,
        strategy_counts=dict(strategy_counts),
    )
