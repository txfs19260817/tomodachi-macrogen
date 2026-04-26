import argparse
import csv
import json
import shutil
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.color_picker import CALIBRATION_COLORS, ColorPicker
from src.living_grid import LivingGridData, load_living_grid_json
from src.macro_writer import MacroWriter
from src.palette import BatchColor, PaletteColor, flatten_batches, make_batches, rgb_to_hsv
from src.path_planner import plan_color_pixels

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.default.json"
OUTPUT_ROOT = ROOT / "out"
RUN_README_TEMPLATE = ROOT / "README_RUN.template.md"


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

    out_dir = resolve_output_dir(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.calibrate_only:
        writer = generate_calibration(config)
        parts = writer.split_output(config.get("split_lines"), config.get("split_frames"))
        part_files = write_parts(out_dir, "calibration_part", parts)
        write_common_outputs(
            out_dir,
            config,
            canvas_size=(256, 256),
            manifest={
                "mode": "calibrate-only",
                "parts": part_files,
                "total_lines": len(writer.lines),
                "total_frames": writer.total_frames(),
            },
        )
        print(f"Wrote calibration macro to {out_dir}")
        return 0

    if args.input is None:
        parser.error(
            "input Living the Grid JSON is required unless --calibrate-only or --clean-output"
        )
    input_path = Path(args.input)
    if input_path.suffix.lower() != ".json":
        parser.error("only Living the Grid JSON input is supported")

    grid = load_living_grid_json(input_path)
    if args.preview_only:
        grid.preview.save(out_dir / "preview_quantized.png")
        write_common_outputs(
            out_dir,
            config,
            canvas_size=(grid.width, grid.height),
            manifest={
                "mode": "preview-only",
                "input": str(input_path),
                "input_source": grid.source,
                "input_version": grid.version,
                "brush": grid.brush,
                "canvas": grid.canvas,
                "preview": "preview_quantized.png",
                "palette_color_count": len(grid.palette),
            },
        )
        print(f"Wrote preview to {out_dir / 'preview_quantized.png'}")
        return 0

    colors = build_living_grid_colors(grid, str(config.get("color_order", "frequency")))
    batches = make_batches(colors, int(config.get("palette_slots", 9)))
    writer = generate_living_grid_macro(config, grid, batches)
    parts = writer.split_output(config.get("split_lines"), config.get("split_frames"))

    grid.preview.save(out_dir / "preview_quantized.png")
    write_palette_report(out_dir / "palette_report.csv", flatten_batches(batches), grid)
    part_files = write_parts(out_dir, "image_part", parts)
    write_common_outputs(
        out_dir,
        config,
        canvas_size=(grid.width, grid.height),
        manifest={
            "mode": str(config.get("mode", "safe-pixel")),
            "input": str(input_path),
            "input_source": grid.source,
            "input_version": grid.version,
            "brush": grid.brush,
            "canvas": grid.canvas,
            "parts": part_files,
            "preview": "preview_quantized.png",
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
        default="out",
        help="Output directory; relative paths are placed under ./out",
    )
    parser.add_argument("--palette-slots", type=int, help="Available game palette slots")
    parser.add_argument(
        "--color-order",
        choices=["frequency", "original-palette", "luminance", "hue"],
        help="Order colors before assigning palette slots",
    )
    parser.add_argument(
        "--mode",
        choices=["safe-pixel", "nearest", "horizontal-runs"],
        help="Drawing path mode",
    )
    parser.add_argument("--split-lines", type=int, help="Maximum macro lines per part")
    parser.add_argument("--split-frames", type=int, help="Maximum frames per part")
    parser.add_argument("--calibrate-only", action="store_true", help="Generate calibration macro")
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
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Only export preview_quantized.png from Living the Grid JSON and exit",
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
        "mode": args.mode,
        "split_lines": args.split_lines,
        "split_frames": args.split_frames,
    }
    for key, value in mapping.items():
        if value is not None:
            config[key] = value


def resolve_output_dir(out_arg: str) -> Path:
    requested = Path(out_arg)
    if requested.is_absolute():
        return requested
    if requested.parts and requested.parts[0].lower() == "out":
        return ROOT / requested
    return OUTPUT_ROOT / requested


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
    path_mode = str(config.get("mode", "safe-pixel"))

    for batch in batches:
        for batch_color in batch:
            palette_entry = grid.palette[batch_color.color.color_index]
            picker.set_palette_slot_press(batch_color.assigned_slot, palette_entry.press)

        for batch_color in batch:
            picker.activate_palette_slot(batch_color.assigned_slot)
            pixels = plan_color_pixels(
                grid.indices,
                batch_color.color.color_index,
                mode=path_mode,
            )
            for x, y in pixels:
                writer.move_cursor_to(x, y)
                writer.draw_pixel()

    return writer


def _luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def generate_calibration(config: dict[str, Any]) -> MacroWriter:
    writer = MacroWriter(config)
    picker = ColorPicker(writer, config)
    palette_slots = int(config.get("palette_slots", 9))

    writer.tap("Y")
    writer.wait(int(config.get("timing", {}).get("menu_open_frames", 8)))
    writer.tap("B")
    writer.wait(int(config.get("timing", {}).get("menu_close_frames", 8)))

    for slot_index in range(palette_slots):
        writer.tap("Y")
        writer.wait(int(config.get("timing", {}).get("menu_open_frames", 8)))
        picker.navigate_to_slot(slot_index)
        writer.tap("B")
        writer.wait(int(config.get("timing", {}).get("menu_close_frames", 8)))

    for slot_index, (_name, rgb) in enumerate(CALIBRATION_COLORS[:palette_slots]):
        picker.set_palette_slot_colour(slot_index, rgb)

    block_size = int(config.get("calibration_block_size", 3))
    columns = 3
    spacing = block_size + 1
    for slot_index in range(min(palette_slots, len(CALIBRATION_COLORS))):
        picker.activate_palette_slot(slot_index, force=True)
        base_x = (slot_index % columns) * spacing
        base_y = (slot_index // columns) * spacing
        for y in range(block_size):
            for x in range(block_size):
                writer.move_cursor_to(base_x + x, base_y + y)
                writer.draw_pixel()

    return writer


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
