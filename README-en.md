# tomodachi-macrogen

Convert [Living the Grid](https://living-the-grid.com/) JSON exports into GLaMS/SwiCC `.txt` macros for Tomodachi Life face paint automation.

This project no longer accepts image input. Living the Grid handles quantization, palette matching, and H/S/B press counts; this tool only generates runnable macros.

Chinese README: [README.md](README.md).

## Workflow

1. Upload an image to Living the Grid.
2. Select `square`, `smooth`, `1px`, and the `game` palette.
3. Set `max colours`, for example `12`.
4. Export `JSON (per-pixel data)`.
5. Generate GLaMS macros with this tool.
6. Run the generated `.txt` files in GLaMS in order.

```bash
uv run python tomodachi_macrogen.py input.json
```

Default output goes to `out/input/`. For example, `abc.json` writes to `out/abc/`.

## Install

```bash
uv venv --python 3.13
uv sync
```

Development checks:

```bash
uv sync --group dev
uv run ruff check .
uv run python -m unittest discover -s tests
```

## Common Commands

```bash
# Generate macros, default split is 50000 lines per part
uv run python tomodachi_macrogen.py input.json

# Disable line splitting
uv run python tomodachi_macrogen.py input.json --split-lines 0

# Split into one file per color
uv run python tomodachi_macrogen.py input.json --split-by-color

# Export preview only
uv run python tomodachi_macrogen.py input.json --preview-only

# Use slower hardware timings
uv run python tomodachi_macrogen.py input.json --config config.slow.json

# Clean generated outputs and caches
uv run python tomodachi_macrogen.py --clean-output --clean-cache
```

## CLI

- `input`: Living the Grid JSON.
- `--out OUT`: output directory; relative paths are placed under project `out/`.
- `--config CONFIG`: extra config JSON overriding `config.default.json`.
- `--palette-slots N`: available in-game palette slots, default `9`.
- `--color-order frequency|original-palette|luminance|hue`: color order, default `original-palette`, matching Living the Grid UI order.
- `--split-lines N`: max lines per part; `0` disables splitting.
- `--split-by-color`: one file per color, useful for rerunning a single color.
- `--calibrate-only`: generate calibration macros only.
- `--preview-only`: generate `preview_quantized.png` only.
- `--clean-output`: delete generated outputs under `out/`.
- `--clean-cache`: delete `.ruff_cache`, `__pycache__`, and similar caches.

The drawing path is fixed to same-color horizontal run planning. Path mode flags were removed.

## Outputs

- `image_part*.txt`: normal macro parts.
- `color_XX_*.txt`: single-color parts from `--split-by-color`.
- `preview_quantized.png`: preview reconstructed from JSON.
- `reconstructed_from_macro.png`: image reconstructed from generated draw coordinates.
- `palette_report.csv`: colors, H/S/B values, pixel counts, and slot assignment.
- `manifest.json`: generation summary.
- `config_used.json`: merged runtime config.
- `README_RUN.md` / `README_RUN-en.md`: run instructions.

## GLaMS

GLaMS: <https://github.com/knflrpn/GLaMS>

This repository keeps GLaMS at `external/GLaMS`:

```bash
git submodule update --init --recursive
git submodule update --remote external/GLaMS
```

Use the standard page `external/GLaMS/macros.html`. Paste generated `.txt` content into the large right-side `commands` textarea. The left-side `recorded-inputs` textarea is for recording output, not for running macros.

To pair the controller, run this first in `commands`:

```text
{A} 10
{} 60
{L1 R1} 10
{} 30
{A} 10
{} 10
```

Run multiple parts one by one in filename order.

## Hardware

- Board A plugs into the Switch / Dock and runs the SwiCC_RP2040 main firmware.
- Board B plugs into the computer and runs `SwiCC_UART_Bridge.uf2`.
- Board A GPIO0/TX connects to Board B GPIO1/RX.
- Board A GPIO1/RX connects to Board B GPIO0/TX.
- Board A GND connects to Board B GND.
- Do not connect 5V or 3V3 between boards.
- For Waveshare RP2040-Zero, wire by GPIO labels, not guessed physical position.

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

Firmware:

- SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040/releases>
- UART bridge: <https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>

To flash UF2, hold `BOOTSEL` while plugging USB, then copy the matching `.uf2` to the `RPI-RP2` drive.

Enable Pro Controller Wired Communication in Switch system settings.

## In-Game Setup

1. Open the face paint drawing screen.
2. Select the thinnest square pixel brush.
3. Move the brush cursor to the top-left first pixel.
4. Do not manually change the selected palette swatch before running, especially with `--split-by-color`.

The generated macro opens the palette, enters the full HSB picker, resets Hue and the color pad, then uses JSON `press.h/s/b` values.

## Config

Defaults live in `config.default.json`. If hardware misses inputs or runs too fast, try:

```bash
uv run python tomodachi_macrogen.py input.json --config config.slow.json
```

Common tuning fields:

- `timing.*`: button, movement, and menu waits.
- `movement_chunk_size` / `movement_chunk_settle_frames`: pauses during long movement.
- `canvas_origin_x` / `canvas_origin_y`: canvas origin offset.
- `split_lines`: default part size.
