from dataclasses import dataclass

from .config import ConfigInput
from .macro_writer import MacroWriter

MACRO_FRAMES_PER_SECOND = 60.0


@dataclass(frozen=True)
class DrawDryRun:
    frame_count: int
    line_count: int
    end_position: tuple[int, int]


def dry_run_draw(
    config: ConfigInput,
    points: list[tuple[int, int]],
    *,
    start: tuple[int, int],
) -> DrawDryRun:
    writer = MacroWriter(config)
    writer.set_canvas_position(*start)
    writer.draw_pixels(points)
    return DrawDryRun(
        frame_count=writer.total_frames(),
        line_count=len(writer.lines),
        end_position=writer.canvas_position(),
    )


def frames_to_seconds(frames: int | float) -> float:
    return float(frames) / MACRO_FRAMES_PER_SECOND


def format_duration(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "--:--"
    total = int(seconds + 0.5)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_frame_duration(frames: int | None) -> str:
    if frames is None:
        return format_duration(None)
    return format_duration(frames_to_seconds(frames))
