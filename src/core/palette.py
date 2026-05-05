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


def rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (channel / 255.0 for channel in rgb)
    hue, saturation, value = colorsys.rgb_to_hsv(r, g, b)
    return (hue * 360.0, saturation, value)
