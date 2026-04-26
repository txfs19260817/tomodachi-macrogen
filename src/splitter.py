from collections.abc import Sequence

from .glams_format import MacroLine


def split_macro_lines(
    macro_lines: Sequence[MacroLine],
    max_lines_per_part: int | None = None,
    max_frames_per_part: int | None = None,
) -> list[list[str]]:
    line_limit = max_lines_per_part if max_lines_per_part and max_lines_per_part > 0 else None
    frame_limit = max_frames_per_part if max_frames_per_part and max_frames_per_part > 0 else None

    if not macro_lines:
        return [[]]
    if line_limit is None and frame_limit is None:
        return [[line.text for line in macro_lines]]

    parts: list[list[MacroLine]] = []
    current: list[MacroLine] = []
    current_frames = 0

    def would_exceed(line: MacroLine) -> bool:
        if not current:
            return False
        if line_limit is not None and len(current) + 1 > line_limit:
            return True
        if frame_limit is not None and current_frames + line.frames > frame_limit:
            return True
        return False

    for line in macro_lines:
        if would_exceed(line):
            split_index = _last_safe_split_index(current)
            if split_index is None:
                parts.append(current)
                current = []
                current_frames = 0
            else:
                parts.append(current[: split_index + 1])
                current = current[split_index + 1 :]
                current_frames = sum(item.frames for item in current)

        current.append(line)
        current_frames += line.frames

    if current:
        parts.append(current)

    return [[line.text for line in part] for part in parts]


def _last_safe_split_index(lines: Sequence[MacroLine]) -> int | None:
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].safe_split_after:
            return index
    return None
