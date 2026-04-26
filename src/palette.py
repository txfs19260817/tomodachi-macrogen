import colorsys
from dataclasses import dataclass


@dataclass(frozen=True)
class PaletteColor:
    color_index: int
    rgb: tuple[int, int, int]
    hsv: tuple[float, float, float]
    pixel_count: int


@dataclass(frozen=True)
class BatchColor:
    color: PaletteColor
    batch_index: int
    assigned_slot: int


def make_batches(colors: list[PaletteColor], palette_slots: int) -> list[list[BatchColor]]:
    if palette_slots < 1:
        raise ValueError("palette_slots must be greater than zero")

    batches: list[list[BatchColor]] = []
    for batch_index, start in enumerate(range(0, len(colors), palette_slots)):
        batch_colors = colors[start : start + palette_slots]
        batches.append(
            [
                BatchColor(color=color, batch_index=batch_index, assigned_slot=slot_index)
                for slot_index, color in enumerate(batch_colors)
            ]
        )
    return batches


def flatten_batches(batches: list[list[BatchColor]]) -> list[BatchColor]:
    return [batch_color for batch in batches for batch_color in batch]


def rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (channel / 255.0 for channel in rgb)
    hue, saturation, value = colorsys.rgb_to_hsv(r, g, b)
    return (hue * 360.0, saturation, value)
