# tomodachi-macrogen

Convert [Living the Grid](https://living-the-grid.com/) JSON exports into SwiCC `.txt` macros for Tomodachi Life face paint automation.

This project no longer accepts image input. Living the Grid handles quantization, palette matching, and H/S/B press counts; this tool only generates runnable macros.

中文文档见 [README-zh.md](README-zh.md)。

## Download

Portable GUI builds are published on the
[GitHub Releases page](https://github.com/txfs19260817/tomodachi-macrogen/releases).
Download the latest asset for your platform, extract it, then run:

- Windows: `tomodachi-gui/tomodachi-gui.exe`
- macOS: `tomodachi-gui.app`
- Linux: `tomodachi-gui/tomodachi-gui`

No installer is produced. The artifacts are unsigned, so Windows/macOS may show the
usual first-run warning.

## GUI Workflow

1. Upload an image to Living the Grid.
2. Select `square`, `smooth`, one of `1px / 3px / 7px / 13px / 19px / 27px`, and the `game` palette.
3. Set `max colours`, for example `12`.
4. Export `JSON (per-pixel data)`.
5. Open `tomodachi-gui`, choose the JSON, and generate macros.
6. Pick the serial port, pair the controller if needed, then start drawing.

## Install

```bash
uv venv --python 3.13
uv sync
```

Development checks:

```bash
uv sync --group dev --group test
uv run ruff check .
uv run pytest -n auto tests
```

## Build Portable GUI Locally

```bash
uv sync --group build
uv run --group build python scripts/build_gui.py
```

Build output goes to `dist/tomodachi-gui/` on Windows/Linux and
`dist/tomodachi-gui.app` on macOS.

GitHub Actions workflow `.github/workflows/python-app.yml` builds portable native GUI
archives on Windows, macOS, and Linux with PyInstaller onedir. Run it manually from
Actions, or push a semantic-version tag such as `v1.0.1`.

Tag releases are the version hook: the workflow validates that `vX.Y.Z` matches
`pyproject.toml`'s project version, then publishes the portable archives as GitHub
Release assets.

## Native GUI

Run `uv run tomodachi-gui` from source, or use the Release build. The GUI provides the
same workflow as the CLI: choose a Living the Grid JSON, generate output, pair the
controller, then send the generated files while showing progress. It renders the JSON
preview, supports Chinese/English plus light/dark themes, and keeps serial work in a
background thread.

## CLI

`tomodachi-macrogen` is the main command. With an input JSON and `--port`, it writes a
timestamped output directory, sends the controller pairing macro, waits 4 seconds, then
sends the generated drawing macros using SwiCC `+Q` encoding and `+GQF` queue polling.

Without `--port`, it only generates files. With `--match-controller` and no input, it only
sends the pairing macro.

Common commands:

```bash
# List serial ports
uv run tomodachi-macrogen --list-ports

# Generate, pair the controller, then draw
uv run tomodachi-macrogen input.json --port COM5 --split-by-color

# Only pair the controller
uv run tomodachi-macrogen --port COM5 --match-controller

# Generate files only, without touching serial
uv run tomodachi-macrogen input.json --split-by-color

# Clean generated outputs and caches
uv run tomodachi-macrogen --clean-output --clean-cache
```

Output always goes to `out/<input-name>-<timestamp>/`.

- `input`: Living the Grid JSON.
- `--port COM5`: generate, pair, and draw through the selected serial port.
- `--list-ports`: list available serial ports.
- `--match-controller`: with no input, only send the controller pairing macro.
- `--config CONFIG`: extra config JSON overriding `config.default.json`.
- `--palette-slots N`: available in-game palette slots, default `9`.
- `--color-order frequency|original-palette|luminance|hue`: color order, default `original-palette`, matching Living the Grid UI order.
- `--split-lines N`: max lines per part; `0` disables splitting.
- `--split-by-color`: one file per color, useful for rerunning a single color.
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

## Hardware

Firmware:

- SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040/releases>
- UART bridge: <https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>

To flash UF2, hold `BOOTSEL` while plugging USB, then copy the matching `.uf2` to the `RPI-RP2` drive.

Enable Pro Controller Wired Communication in Switch system settings.

- Board A plugs into the Switch / Dock and runs the SwiCC_RP2040 main firmware.
- Board B plugs into the computer and runs `SwiCC_UART_Bridge.uf2`.
- Board A GPIO0/TX connects to Board B GPIO1/RX.
- Board A GPIO1/RX connects to Board B GPIO0/TX.
- Board A GND connects to Board B GND.
- Do not connect 5V or 3V3 between boards.
- For Waveshare RP2040-Zero, wire by GPIO labels, not guessed physical position.

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

## In-Game Setup

1. Open the face paint drawing screen.
2. Select the same square smooth brush size shown in the Living the Grid JSON.
3. For normal `image_part*.txt`, move the brush cursor to the top-left first pixel first.
4. Do not manually change the selected palette swatch before running, especially with `--split-by-color`.

The generated macro treats one Living the Grid cell as one brush stamp; movement is scaled by `brush.px`. If every used palette entry includes `game: {row, col}`, `game: {extra}`, or a label like `R1·C1`, the macro stays on the default 84-color Game Palette. Otherwise it opens the H/S/B picker and uses JSON `press.h/s/b` values. Each `color_*.txt` starts with a hard canvas reset: hold the stick upper-left for 7 seconds, then move right 192 and down 77.

## Config

Defaults live in `config.default.json`. Current defaults are intentionally conservative to avoid missed inputs on hardware.

Common tuning fields:

- `timing.*`: button, movement, and menu waits.
- `game_palette_*`: dimensions and anchor timing for default Game Palette navigation.
- `movement_chunk_size` / `movement_chunk_settle_frames`: pauses during long movement.
- `canvas_reset_right_steps` / `canvas_reset_down_steps`: recovery steps after the `color_*.txt` hard reset.
- `timing.canvas_reset_*`: stick hold and settle timing for the `color_*.txt` hard reset.
- `split_lines`: default part size.

## References

- Living the Grid: <https://living-the-grid.com/>
- SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040>
- Waveshare RP2040-Zero pinout: <https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg>
- TomodachiDraw picker navigation reference: <https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/CanvasNavigatorService.cs>
