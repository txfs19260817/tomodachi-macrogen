import pytest

from benchmarks.path_benchmark_helpers import (
    benchmark_auto_tsp_limit,
    load_fixture_cases,
)
from src.macro_timing import frames_to_seconds

FIXTURE_CASES = load_fixture_cases()
TSP_LIMITS = (0, 120, 400, 800, 1200)


@pytest.mark.benchmark(group="tsp limit tuning")
@pytest.mark.parametrize("fixture_name", tuple(FIXTURE_CASES))
@pytest.mark.parametrize("path_tsp_max_runs", TSP_LIMITS)
def test_tsp_limit_tuning(
    benchmark: object,
    fixture_name: str,
    path_tsp_max_runs: int,
) -> None:
    case = FIXTURE_CASES[fixture_name]

    summary = benchmark.pedantic(
        benchmark_auto_tsp_limit,
        args=(case,),
        kwargs={"tsp_max_runs": path_tsp_max_runs},
        iterations=1,
        rounds=1,
    )
    benchmark.extra_info["fixture"] = fixture_name
    benchmark.extra_info["path_tsp_max_runs"] = path_tsp_max_runs
    benchmark.extra_info["total_frames"] = summary.total_frames
    benchmark.extra_info["total_seconds"] = frames_to_seconds(summary.total_frames)
    benchmark.extra_info["saved_frames"] = summary.saved_frames
    benchmark.extra_info["saved_seconds"] = frames_to_seconds(summary.saved_frames)
    benchmark.extra_info["strategy_counts"] = summary.strategy_counts

    assert summary.total_frames > 0
