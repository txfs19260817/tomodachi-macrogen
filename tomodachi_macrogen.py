import argparse
import csv
import json
import shutil
import sys
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from src.color_picker import ColorPicker
from src.living_grid import LivingGridData, load_living_grid_json
from src.macro_writer import MacroWriter
from src.palette import BatchColor, PaletteColor, flatten_batches, make_batches, rgb_to_hsv
from src.path_planner import plan_color_pixels
from swicc_runner import (
    build_command_list,
    import_serial_tools,
    run_serial_transfer,
)

SOURCE_ROOT = Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
DEFAULT_CONFIG = RESOURCE_ROOT / "config.default.json"
RUN_README_TEMPLATE = RESOURCE_ROOT / "README_RUN.template.md"
RUN_README_EN_TEMPLATE = RESOURCE_ROOT / "README_RUN-en.template.md"


@dataclass(frozen=True)
class GenerationOptions:
    config_path: str | Path | None = None
    output_root: str | Path | None = None
    timestamp: str | None = None
    palette_slots: int | None = None
    color_order: str | None = None
    split_lines: int | None = None
    split_by_color: bool = False


@dataclass(frozen=True)
class GenerationResult:
    input_path: Path
    out_dir: Path
    preview_path: Path
    reconstructed_path: Path
    manifest_path: Path
    macro_files: list[Path]
    manifest: dict[str, Any]

    @property
    def total_lines(self) -> int:
        return int(self.manifest.get("total_lines", 0))

    @property
    def total_frames(self) -> int:
        return int(self.manifest.get("total_frames", 0))


@dataclass(frozen=True)
class SerialOptions:
    baud_rate: int = 115200
    vsync_delay: int = -1
    batch_size: int = 60
    queue_threshold: int = 60
    response_timeout: float = 5.0
    poll_interval: float = 0.25


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_ports:
        return list_ports()

    did_clean = False
    if args.clean_output:
        clean_output()
        print(f"Cleaned output directory: {default_output_root()}")
        did_clean = True
    if args.clean_cache:
        clean_cache()
        print("Cleaned local Python/tool caches")
        did_clean = True
    if did_clean:
        return 0

    serial_options = SerialOptions(
        baud_rate=args.baud_rate,
        vsync_delay=args.vsync_delay,
        batch_size=args.batch_size,
        queue_threshold=args.queue_threshold,
        response_timeout=args.response_timeout,
        poll_interval=args.poll_interval,
    )

    if args.match_controller and not args.port:
        parser.error("--port is required for --match-controller")

    if args.input is None:
        if args.match_controller:
            send_macro_files(
                port=args.port,
                files=[],
                match_controller=True,
                serial_options=serial_options,
            )
            return 0
        parser.error("input Living the Grid JSON is required unless cleaning outputs/caches")

    result = generate_macros(
        args.input,
        GenerationOptions(
            config_path=args.config,
            palette_slots=args.palette_slots,
            color_order=args.color_order,
            split_lines=args.split_lines,
            split_by_color=args.split_by_color,
        ),
    )
    if args.split_by_color:
        print(f"Wrote color-split Living the Grid macros to {result.out_dir}")
    else:
        print(f"Wrote Living the Grid macro to {result.out_dir}")
    if args.port:
        print("Pairing controller and sending drawing macros...")
        send_macro_files(
            port=args.port,
            files=result.macro_files,
            match_controller=True,
            serial_options=serial_options,
        )
    else:
        print("No --port provided; generated files only.")
    return 0


def clean_main() -> int:
    parser = argparse.ArgumentParser(description="Clean generated outputs and local caches.")
    parser.add_argument(
        "--output",
        action="store_true",
        help="Clean generated output directories under out/.",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Clean local Python/tool caches.",
    )
    args = parser.parse_args()

    clean_outputs = args.output or not args.cache
    clean_caches = args.cache or not args.output
    if clean_outputs:
        clean_output()
        print(f"Cleaned output directory: {default_output_root()}")
    if clean_caches:
        clean_cache()
        print("Cleaned local Python/tool caches")
    return 0


def generate_macros(
    input_file: str | Path,
    options: GenerationOptions | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> GenerationResult:
    options = options or GenerationOptions()
    input_path = Path(input_file)
    if input_path.suffix.lower() != ".json":
        raise ValueError("only Living the Grid JSON input is supported")

    config = load_config(options.config_path)
    apply_generation_overrides(config, options)

    out_dir = resolve_output_dir(
        input_path,
        output_root=(
            Path(options.output_root)
            if options.output_root is not None
            else default_output_root()
        ),
        timestamp=options.timestamp,
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    report_generation_progress(progress_callback, "status.loading_json")
    grid = load_living_grid_json(input_path)
    config.setdefault("canvas_cell_step", grid.brush_px)
    colors = build_living_grid_colors(grid, str(config.get("color_order", "original-palette")))
    batches = make_batches(colors, int(config.get("palette_slots", 9)))
    direct_palette = has_game_palette_coordinates(grid, colors)
    palette_source = "game" if direct_palette else "auto"

    report_generation_progress(progress_callback, "status.planning_macros")
    grid.preview.save(out_dir / "preview_quantized.png")
    if options.split_by_color:
        writers = generate_color_split_macros(config, grid, colors)
        part_files = write_color_parts(out_dir, writers, grid)
        reconstructed = reconstruct_color_split_image(grid, writers)
        reconstructed.save(out_dir / "reconstructed_from_macro.png")
        report_generation_progress(progress_callback, "status.writing_output")
        write_palette_report(out_dir / "palette_report.csv", color_split_report(colors), grid)
        manifest = write_common_outputs(
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
                "canvas_cell_step": config.get("canvas_cell_step"),
                "palette_source": palette_source,
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
        return build_generation_result(input_path, out_dir, manifest)

    writer = (
        generate_direct_palette_macro(config, grid, colors)
        if direct_palette
        else generate_living_grid_macro(config, grid, batches)
    )
    parts = writer.split_output(config.get("split_lines"))
    batch_colors = color_split_report(colors) if direct_palette else flatten_batches(batches)
    reconstructed = reconstruct_batched_image(grid, writer, batch_colors)
    reconstructed.save(out_dir / "reconstructed_from_macro.png")

    report_generation_progress(progress_callback, "status.writing_output")
    write_palette_report(out_dir / "palette_report.csv", batch_colors, grid)
    part_files = write_parts(out_dir, "image_part", parts)
    manifest = write_common_outputs(
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
            "canvas_cell_step": config.get("canvas_cell_step"),
            "palette_source": palette_source,
            "parts": part_files,
            "preview": "preview_quantized.png",
            "reconstructed": "reconstructed_from_macro.png",
            "palette_report": "palette_report.csv",
            "palette_color_count": len(colors),
            "batch_count": 0 if direct_palette else len(batches),
            "total_lines": len(writer.lines),
            "total_frames": writer.total_frames(),
        },
    )
    return build_generation_result(input_path, out_dir, manifest)


def report_generation_progress(
    progress_callback: Callable[[str], None] | None,
    status_key: str,
) -> None:
    if progress_callback is not None:
        progress_callback(status_key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Living the Grid macros, pair the controller, and send them."
    )
    parser.add_argument("input", nargs="?", help="Living the Grid JSON file")
    parser.add_argument("--config", help="Path to config JSON")
    parser.add_argument("--port", help="Serial port, for example COM5 or /dev/ttyACM0")
    parser.add_argument("--list-ports", action="store_true", help="List serial ports and exit")
    parser.add_argument(
        "--match-controller",
        action="store_true",
        help="With no input, only send the controller pairing macro",
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
            "Write one macro txt per color; each file sets slot 0 and starts from a "
            "hard canvas reset"
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
    parser.add_argument("--baud-rate", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--vsync-delay", type=int, default=-1, help="-1 disables VSYNC delay")
    parser.add_argument("--batch-size", type=int, default=60, help="Max +Q lines to send per batch")
    parser.add_argument(
        "--queue-threshold",
        type=int,
        default=60,
        help="Send the next batch when SwiCC queue fill is below this value",
    )
    parser.add_argument(
        "--response-timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for a +GQF response before failing",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.25,
        help="Seconds between queue fill checks",
    )
    return parser


def list_ports() -> int:
    serial_tools = import_serial_tools()
    ports = list(serial_tools.comports())
    if not ports:
        print("No serial ports found.")
        return 0
    for port in ports:
        details = f" - {port.description}" if port.description else ""
        print(f"{port.device}{details}")
    return 0


def send_macro_files(
    *,
    port: str,
    files: list[Path],
    match_controller: bool,
    serial_options: SerialOptions | None = None,
    progress_callback: Any | None = None,
    should_cancel: Any | None = None,
    show_progress_bar: bool = True,
) -> None:
    serial_options = serial_options or SerialOptions()
    commands = build_command_list(files, match_controller=match_controller)
    run_serial_transfer(
        port=port,
        commands=commands,
        baud_rate=serial_options.baud_rate,
        vsync_delay=serial_options.vsync_delay,
        batch_size=serial_options.batch_size,
        queue_threshold=serial_options.queue_threshold,
        response_timeout=serial_options.response_timeout,
        poll_interval=serial_options.poll_interval,
        progress_callback=progress_callback,
        should_cancel=should_cancel,
        show_progress_bar=show_progress_bar,
    )


def load_config(config_path: str | Path | None) -> dict[str, Any]:
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


def apply_generation_overrides(config: dict[str, Any], options: GenerationOptions) -> None:
    mapping = {
        "palette_slots": options.palette_slots,
        "color_order": options.color_order,
        "split_lines": options.split_lines,
    }
    for key, value in mapping.items():
        if value is not None:
            config[key] = value


def resolve_output_dir(
    input_path: Path,
    *,
    output_root: Path | None = None,
    timestamp: str | None = None,
) -> Path:
    output_root = output_root or default_output_root()
    suffix = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    requested = output_root / f"{default_output_name(input_path)}-{suffix}"
    return unique_output_dir(requested)


def unique_output_dir(requested: Path) -> Path:
    if not requested.exists():
        return requested
    for index in range(2, 1000):
        candidate = requested.with_name(f"{requested.name}-{index}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"too many existing output directories for {requested}")


def default_output_name(input_path: Path) -> str:
    return input_path.stem or "output"


def default_output_root(
    *,
    frozen: bool | None = None,
    executable: str | Path | None = None,
) -> Path:
    is_frozen = bool(getattr(sys, "frozen", False) if frozen is None else frozen)
    if not is_frozen:
        return SOURCE_ROOT / "out"

    exe_path = Path(executable or sys.executable).resolve()
    if (
        exe_path.parent.name == "MacOS"
        and exe_path.parent.parent.name == "Contents"
        and exe_path.parent.parent.parent.suffix == ".app"
    ):
        return exe_path.parent.parent.parent.parent / "out"
    return exe_path.parent / "out"


def clean_output() -> None:
    output_root = default_output_root()
    output_root.mkdir(parents=True, exist_ok=True)
    for child in output_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def clean_cache() -> None:
    for cache_dir in [SOURCE_ROOT / ".ruff_cache", SOURCE_ROOT / ".pytest_cache"]:
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
    for pycache_dir in SOURCE_ROOT.rglob("__pycache__"):
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
            writer.draw_pixels(pixels)

    return writer


def generate_direct_palette_macro(
    config: dict[str, Any],
    grid: LivingGridData,
    colors: list[PaletteColor],
) -> MacroWriter:
    writer = MacroWriter(config)
    picker = ColorPicker(writer, config)

    for color in colors:
        palette_entry = grid.palette[color.color_index]
        select_current_color(picker, config, palette_entry)
        pixels = plan_color_pixels(
            grid.indices,
            color.color_index,
            start=writer.canvas_position(),
        )
        writer.draw_pixels(pixels)

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

        select_current_color(picker, config, palette_entry)
        writer.reset_canvas_to_origin()
        pixels = plan_color_pixels(
            grid.indices,
            color.color_index,
            start=writer.canvas_position(),
        )
        writer.draw_pixels(pixels)

        writers.append((color, writer))

    return writers


def has_game_palette_coordinates(
    grid: LivingGridData,
    colors: list[PaletteColor],
) -> bool:
    return bool(colors) and all(
        grid.palette[color.color_index].game is not None for color in colors
    )


def select_current_color(picker: ColorPicker, config: dict[str, Any], palette_entry: Any) -> None:
    del config
    if palette_entry.game is not None:
        picker.set_current_palette_slot_game(palette_entry.game)
        return
    picker.set_current_palette_slot_press(palette_entry.press)


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
) -> dict[str, Any]:
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
    return manifest


def build_generation_result(
    input_path: Path,
    out_dir: Path,
    manifest: dict[str, Any],
) -> GenerationResult:
    return GenerationResult(
        input_path=input_path,
        out_dir=out_dir,
        preview_path=out_dir / str(manifest["preview"]),
        reconstructed_path=out_dir / str(manifest["reconstructed"]),
        manifest_path=out_dir / "manifest.json",
        macro_files=[out_dir / str(part["file"]) for part in manifest.get("parts", [])],
        manifest=manifest,
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
