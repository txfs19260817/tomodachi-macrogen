import argparse
import csv
import json
import shutil
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from src.color_picker import ColorPicker
from src.living_grid import LivingGridData, load_living_grid_json
from src.macro_writer import MacroWriter
from src.palette import BatchColor, PaletteColor, flatten_batches, make_batches, rgb_to_hsv
from src.path_planner import plan_color_pixels

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.default.json"
OUTPUT_ROOT = ROOT / "out"
RUN_README_TEMPLATE = ROOT / "README_RUN.template.md"
RUN_README_EN_TEMPLATE = ROOT / "README_RUN-en.template.md"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    did_clean = False
    if args.clean_output:
        clean_output()
        print(f"Cleaned output directory: {OUTPUT_ROOT}")
        did_clean = True
    if args.clean_cache:
        clean_cache()
        print("Cleaned local Python/tool caches")
        did_clean = True
    if did_clean:
        return 0

    config = load_config(args.config)
    apply_cli_overrides(config, args)

    if args.input is None:
        parser.error("input Living the Grid JSON is required unless cleaning outputs/caches")
    input_path = Path(args.input)
    if input_path.suffix.lower() != ".json":
        parser.error("only Living the Grid JSON input is supported")

    out_dir = resolve_output_dir(args.out, input_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    grid = load_living_grid_json(input_path)
    colors = build_living_grid_colors(grid, str(config.get("color_order", "original-palette")))
    batches = make_batches(colors, int(config.get("palette_slots", 9)))

    grid.preview.save(out_dir / "preview_quantized.png")
    if args.split_by_color:
        writers = generate_color_split_macros(config, grid, colors)
        part_files = write_color_parts(out_dir, writers, grid)
        reconstructed = reconstruct_color_split_image(grid, writers)
        reconstructed.save(out_dir / "reconstructed_from_macro.png")
        write_palette_report(out_dir / "palette_report.csv", color_split_report(colors), grid)
        write_common_outputs(
            out_dir,
            config,
            canvas_size=(grid.width, grid.height),
            manifest={
                "mode": "living-grid",
                "path_strategy": "nearest-runs",
                "split_strategy": "color",
                "input": str(input_path),
                "input_source": grid.source,
                "input_version": grid.version,
                "brush": grid.brush,
                "canvas": grid.canvas,
                "parts": part_files,
                "preview": "preview_quantized.png",
                "reconstructed": "reconstructed_from_macro.png",
                "palette_report": "palette_report.csv",
                "palette_color_count": len(colors),
                "batch_count": 0,
                "total_lines": sum(len(writer.lines) for _color, writer in writers),
                "total_frames": sum(writer.total_frames() for _color, writer in writers),
            },
        )
        print(f"Wrote color-split Living the Grid macros to {out_dir}")
        return 0

    writer = generate_living_grid_macro(config, grid, batches)
    parts = writer.split_output(config.get("split_lines"))
    reconstructed = reconstruct_batched_image(grid, writer, flatten_batches(batches))
    reconstructed.save(out_dir / "reconstructed_from_macro.png")

    write_palette_report(out_dir / "palette_report.csv", flatten_batches(batches), grid)
    part_files = write_parts(out_dir, "image_part", parts)
    write_common_outputs(
        out_dir,
        config,
        canvas_size=(grid.width, grid.height),
        manifest={
            "mode": "living-grid",
            "path_strategy": "nearest-runs",
            "split_strategy": "lines",
            "input": str(input_path),
            "input_source": grid.source,
            "input_version": grid.version,
            "brush": grid.brush,
            "canvas": grid.canvas,
            "parts": part_files,
            "preview": "preview_quantized.png",
            "reconstructed": "reconstructed_from_macro.png",
            "palette_report": "palette_report.csv",
            "palette_color_count": len(colors),
            "batch_count": len(batches),
            "total_lines": len(writer.lines),
            "total_frames": writer.total_frames(),
        },
    )
    print(f"Wrote Living the Grid macro to {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate GLaMS/SwiCC macro scripts from Living the Grid JSON."
    )
    parser.add_argument("input", nargs="?", help="Living the Grid JSON file")
    parser.add_argument("--config", help="Path to config JSON")
    parser.add_argument(
        "--out",
        help=(
            "Output directory; defaults to the input filename without extension. "
            "Relative paths are placed under ./out"
        ),
    )
    parser.add_argument("--palette-slots", type=int, help="Available game palette slots")
    parser.add_argument(
        "--color-order",
        choices=["frequency", "original-palette", "luminance", "hue"],
        help="Order colors before assigning palette slots",
    )
    parser.add_argument(
        "--split-lines",
        type=int,
        help="Maximum macro lines per part; 0 disables line-based splitting",
    )
    parser.add_argument(
        "--split-by-color",
        action="store_true",
        help=(
            "Write one macro txt per color; each file sets slot 0, draws that color, "
            "then returns to top-left"
        ),
    )
    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Delete generated files under the project out directory and exit",
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="Delete local Python/tool caches and exit",
    )
    return parser


def load_config(config_path: str | None) -> dict[str, Any]:
    with DEFAULT_CONFIG.open("r", encoding="utf-8") as file:
        config = json.load(file)
    if config_path:
        with Path(config_path).open("r", encoding="utf-8") as file:
            config = deep_merge(config, json.load(file))
    return config


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def apply_cli_overrides(config: dict[str, Any], args: argparse.Namespace) -> None:
    mapping = {
        "palette_slots": args.palette_slots,
        "color_order": args.color_order,
        "split_lines": args.split_lines,
    }
    for key, value in mapping.items():
        if value is not None:
            config[key] = value


def resolve_output_dir(out_arg: str | None, input_path: Path) -> Path:
    requested = Path(out_arg) if out_arg is not None else Path(default_output_name(input_path))
    if requested.is_absolute():
        return requested
    if requested.parts and requested.parts[0].lower() == "out":
        return ROOT / requested
    return OUTPUT_ROOT / requested


def default_output_name(input_path: Path) -> str:
    return input_path.stem or "output"


def clean_output() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for child in OUTPUT_ROOT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def clean_cache() -> None:
    for cache_dir in [ROOT / ".ruff_cache", ROOT / ".pytest_cache"]:
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
    for pycache_dir in ROOT.rglob("__pycache__"):
        if ".venv" not in pycache_dir.parts:
            shutil.rmtree(pycache_dir)


def build_living_grid_colors(grid: LivingGridData, order: str) -> list[PaletteColor]:
    colors = [
        PaletteColor(
            color_index=entry.color_index,
            rgb=entry.rgb,
            hsv=rgb_to_hsv(entry.rgb),
            pixel_count=entry.pixel_count,
        )
        for entry in grid.palette
        if entry.pixel_count > 0
    ]
    if order == "frequency":
        return sorted(colors, key=lambda color: (-color.pixel_count, color.color_index))
    if order == "luminance":
        return sorted(colors, key=lambda color: (_luminance(color.rgb), color.color_index))
    if order == "hue":
        return sorted(colors, key=lambda color: (color.hsv[0], color.hsv[1], color.hsv[2]))
    return colors


def generate_living_grid_macro(
    config: dict[str, Any],
    grid: LivingGridData,
    batches: list[list[BatchColor]],
) -> MacroWriter:
    writer = MacroWriter(config)
    picker = ColorPicker(writer, config)

    for batch in batches:
        for batch_color in batch:
            palette_entry = grid.palette[batch_color.color.color_index]
            picker.set_palette_slot_press(batch_color.assigned_slot, palette_entry.press)

        for batch_color in batch:
            picker.activate_palette_slot(batch_color.assigned_slot)
            pixels = plan_color_pixels(
                grid.indices,
                batch_color.color.color_index,
                start=writer.canvas_position(),
            )
            for x, y in pixels:
                writer.move_cursor_to(x, y)
                writer.draw_pixel()

    return writer


def generate_color_split_macros(
    config: dict[str, Any],
    grid: LivingGridData,
    colors: list[PaletteColor],
) -> list[tuple[PaletteColor, MacroWriter]]:
    writers: list[tuple[PaletteColor, MacroWriter]] = []

    for color in colors:
        writer = MacroWriter(config)
        picker = ColorPicker(writer, config)
        palette_entry = grid.palette[color.color_index]

        picker.set_current_palette_slot_press(palette_entry.press)
        writer.reset_canvas_to_origin()
        for x, y in plan_color_pixels(
            grid.indices,
            color.color_index,
            start=writer.canvas_position(),
        ):
            writer.move_cursor_to(x, y)
            writer.draw_pixel()

        writers.append((color, writer))

    return writers


def color_split_report(colors: list[PaletteColor]) -> list[BatchColor]:
    return [
        BatchColor(color=color, batch_index=index, assigned_slot=0)
        for index, color in enumerate(colors)
    ]


def reconstruct_color_split_image(
    grid: LivingGridData,
    writers: list[tuple[PaletteColor, MacroWriter]],
) -> Image.Image:
    image = Image.new("RGBA", (grid.width, grid.height), (0, 0, 0, 0))
    pixels = image.load()
    for color, writer in writers:
        rgba = (*color.rgb, 255)
        for x, y in writer.draw_events:
            if 0 <= x < grid.width and 0 <= y < grid.height:
                pixels[x, y] = rgba
    return image


def reconstruct_batched_image(
    grid: LivingGridData,
    writer: MacroWriter,
    batch_colors: list[BatchColor],
) -> Image.Image:
    image = Image.new("RGBA", (grid.width, grid.height), (0, 0, 0, 0))
    pixels = image.load()
    event_index = 0
    for batch_color in batch_colors:
        rgba = (*batch_color.color.rgb, 255)
        for _ in range(batch_color.color.pixel_count):
            if event_index >= len(writer.draw_events):
                break
            x, y = writer.draw_events[event_index]
            event_index += 1
            if 0 <= x < grid.width and 0 <= y < grid.height:
                pixels[x, y] = rgba
    return image


def _luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def write_parts(out_dir: Path, prefix: str, parts: list[list[str]]) -> list[dict[str, Any]]:
    written: list[dict[str, Any]] = []
    for index, lines in enumerate(parts, start=1):
        filename = f"{prefix}{index}.txt"
        path = out_dir / filename
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(
            {
                "file": filename,
                "line_count": len(lines),
                "frame_count": sum(_line_frames(line) for line in lines),
            }
        )
    return written


def write_color_parts(
    out_dir: Path,
    writers: list[tuple[PaletteColor, MacroWriter]],
    grid: LivingGridData,
) -> list[dict[str, Any]]:
    written: list[dict[str, Any]] = []
    for index, (color, writer) in enumerate(writers, start=1):
        entry = grid.palette[color.color_index]
        filename = f"color_{index:02d}_{entry.hex.lstrip('#')}.txt"
        path = out_dir / filename
        lines = [line.text for line in writer.lines]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(
            {
                "file": filename,
                "line_count": len(lines),
                "frame_count": writer.total_frames(),
                "color_index": color.color_index,
                "hex": entry.hex,
                "pixel_count": color.pixel_count,
                "assigned_slot": 0,
            }
        )
    return written


def write_palette_report(
    path: Path,
    batch_colors: list[BatchColor],
    grid: LivingGridData,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "color_index",
                "hex",
                "rgb",
                "hsv",
                "press_h",
                "press_s",
                "press_b",
                "pixel_count",
                "assigned_slot",
                "batch_index",
            ],
        )
        writer.writeheader()
        for batch_color in batch_colors:
            color = batch_color.color
            entry = grid.palette[color.color_index]
            writer.writerow(
                {
                    "color_index": color.color_index,
                    "hex": entry.hex,
                    "rgb": f"{color.rgb[0]},{color.rgb[1]},{color.rgb[2]}",
                    "hsv": f"{color.hsv[0]:.3f},{color.hsv[1]:.6f},{color.hsv[2]:.6f}",
                    "press_h": entry.press.h,
                    "press_s": entry.press.s,
                    "press_b": entry.press.b,
                    "pixel_count": color.pixel_count,
                    "assigned_slot": batch_color.assigned_slot,
                    "batch_index": batch_color.batch_index,
                }
            )


def write_common_outputs(
    out_dir: Path,
    config: dict[str, Any],
    canvas_size: tuple[int, int],
    manifest: dict[str, Any],
) -> None:
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "generator": "tomodachi-macrogen",
        "canvas_width": canvas_size[0],
        "canvas_height": canvas_size[1],
        **manifest,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "config_used.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README_RUN.md").write_text(
        RUN_README_TEMPLATE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (out_dir / "README_RUN-en.md").write_text(
        RUN_README_EN_TEMPLATE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _line_frames(line: str) -> int:
    parts = line.strip().split()
    if not parts:
        return 0
    try:
        return int(parts[-1])
    except ValueError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
