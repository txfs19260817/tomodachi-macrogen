import pytest

from benchmarks.path_benchmark_helpers import (
    benchmark_single_strategy,
    load_fixture_cases,
    planner_strategy_names,
)
from src.core.path_planner import get_path_strategy
from src.macro.macro_timing import frames_to_seconds

FIXTURE_CASES = load_fixture_cases()
PLANNER_STRATEGIES = planner_strategy_names()
PLANNER_COMPARE_TSP_MAX_RUNS = 1200


@pytest.mark.benchmark(group="planner strategy comparison")
@pytest.mark.parametrize("fixture_name", tuple(FIXTURE_CASES))
@pytest.mark.parametrize("strategy_name", PLANNER_STRATEGIES)
def test_planner_strategy_comparison(
    benchmark: object,
    fixture_name: str,
    strategy_name: str,
) -> None:
    case = FIXTURE_CASES[fixture_name]
    strategy = get_path_strategy(strategy_name)

    summary = benchmark.pedantic(
        benchmark_single_strategy,
        args=(case, strategy),
        kwargs={"tsp_max_runs": PLANNER_COMPARE_TSP_MAX_RUNS},
        iterations=1,
        rounds=1,
    )
    benchmark.extra_info["fixture"] = fixture_name
    benchmark.extra_info["strategy"] = strategy_name
    benchmark.extra_info["total_frames"] = summary.total_frames
    benchmark.extra_info["total_seconds"] = frames_to_seconds(summary.total_frames)
    benchmark.extra_info["strategy_counts"] = summary.strategy_counts

    assert summary.total_frames > 0
