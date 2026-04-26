from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


@dataclass(frozen=True)
class PressCounts:
    h: int
    s: int
    b: int


@dataclass(frozen=True)
class LivingGridPaletteEntry:
    color_index: int
    hex: str
    rgb: tuple[int, int, int]
    press: PressCounts
    pixel_count: int


@dataclass(frozen=True)
class LivingGridData:
    source: str
    version: int
    width: int
    height: int
    brush: dict[str, Any]
    canvas: dict[str, Any]
    palette: list[LivingGridPaletteEntry]
    indices: list[list[int]]
    preview: Image.Image


def load_living_grid_json(path: str | Path) -> LivingGridData:
    import json

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_root(data)
    width = int(data["width"])
    height = int(data["height"])
    raw_palette = data["palette"]
    raw_pixels = data["pixels"]

    counts = _count_pixels(raw_pixels, len(raw_palette), width, height)
    palette = [
        _parse_palette_entry(index, entry, counts.get(index, 0))
        for index, entry in enumerate(raw_palette)
    ]
    preview = _make_preview(width, height, raw_pixels, palette)

    return LivingGridData(
        source=data["source"],
        version=int(data["version"]),
        width=width,
        height=height,
        brush=dict(data.get("brush", {})),
        canvas=dict(data.get("canvas", {})),
        palette=palette,
        indices=raw_pixels,
        preview=preview,
    )


def _validate_root(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("Living the Grid JSON must be an object")
    if data.get("source") != "living-the-grid.com":
        raise ValueError("JSON source must be living-the-grid.com")
    if int(data.get("version", 0)) < 1:
        raise ValueError("unsupported Living the Grid JSON version")
    width = data.get("width")
    height = data.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise ValueError("Living the Grid JSON must include positive integer width/height")
    if not isinstance(data.get("palette"), list) or not data["palette"]:
        raise ValueError("Living the Grid JSON must include a non-empty palette")
    if not isinstance(data.get("pixels"), list):
        raise ValueError("Living the Grid JSON must include pixels")


def _parse_palette_entry(
    color_index: int,
    entry: Any,
    pixel_count: int,
) -> LivingGridPaletteEntry:
    if not isinstance(entry, dict):
        raise ValueError(f"palette[{color_index}] must be an object")
    rgb = entry.get("rgb")
    press = entry.get("press")
    if (
        not isinstance(rgb, list)
        or len(rgb) != 3
        or any(not isinstance(value, int) or value < 0 or value > 255 for value in rgb)
    ):
        raise ValueError(f"palette[{color_index}].rgb must contain three 0..255 integers")
    if not isinstance(press, dict):
        raise ValueError(f"palette[{color_index}].press is required")
    press_counts = PressCounts(
        h=_parse_press(press, "h", color_index),
        s=_parse_press(press, "s", color_index),
        b=_parse_press(press, "b", color_index),
    )
    return LivingGridPaletteEntry(
        color_index=color_index,
        hex=str(entry.get("hex", "")),
        rgb=(int(rgb[0]), int(rgb[1]), int(rgb[2])),
        press=press_counts,
        pixel_count=pixel_count,
    )


def _parse_press(press: dict[str, Any], key: str, color_index: int) -> int:
    value = press.get(key)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"palette[{color_index}].press.{key} must be a non-negative integer")
    return value


def _count_pixels(
    pixels: Any,
    palette_size: int,
    width: int,
    height: int,
) -> dict[int, int]:
    if len(pixels) != height:
        raise ValueError(f"pixels must contain {height} rows")
    counts: dict[int, int] = {}
    for y, row in enumerate(pixels):
        if not isinstance(row, list) or len(row) != width:
            raise ValueError(f"pixels[{y}] must contain {width} columns")
        for value in row:
            if not isinstance(value, int) or value < 0 or value >= palette_size:
                raise ValueError(f"pixel index {value!r} is outside palette range")
            counts[value] = counts.get(value, 0) + 1
    return counts


def _make_preview(
    width: int,
    height: int,
    pixels: list[list[int]],
    palette: list[LivingGridPaletteEntry],
) -> Image.Image:
    image = Image.new("RGBA", (width, height))
    preview_pixels: list[tuple[int, int, int, int]] = []
    for row in pixels:
        for color_index in row:
            r, g, b = palette[color_index].rgb
            preview_pixels.append((r, g, b, 255))
    image.putdata(preview_pixels)
    return image
