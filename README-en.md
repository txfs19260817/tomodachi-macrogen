# tomodachi-macrogen

PC-side Python 3.13+ macro generator for Tomodachi Life / Tomodachi Life: Living the Dream face paint automation.

This tool now accepts only JSON exported by [Living the Grid](https://living-the-grid.com/). Image quantization, game-palette matching, and H/S/B press counts are handled by Living the Grid; this tool converts the JSON into GLaMS/SwiCC `.txt` macro scripts.

The reason is practical: Living the Grid's `game` palette and H/S/B press counts target the game's non-linear color picker. That is more reliable than local quantization plus naive HSV conversion.

## Recommended Workflow

1. Open <https://living-the-grid.com/>.
2. Upload your image.
3. Select `square`.
4. Select `smooth`.
5. Select `1px`.
6. Set `max colours = 12` or your preferred color count.
7. Select the `game` palette.
8. Export `JSON (per-pixel data)`.
9. Run this tool on that JSON.

Example:

```bash
uv run python tomodachi_macrogen.py C:\Users\duola\Downloads\living-the-grid-1777233657767.json --out doll
```

Relative outputs are placed under the project-level `out/` directory, so this writes to:

```text
out/doll
```

## Hardware Workflow

- Board A: plug into the Switch or Switch 2 Dock and flash the SwiCC_RP2040 main firmware. It emulates a Switch Pro Controller.
- Board B: plug into the computer over USB and flash `SwiCC_UART_Bridge.uf2`. It acts as the USB-UART bridge.
- Board A GPIO0/TX -> Board B GPIO1/RX.
- Board A GPIO1/RX -> Board B GPIO0/TX.
- Board A GND -> Board B GND.
- Do not connect 5V or 3V3 between the boards.

Enable Pro Controller Wired Communication in the Switch / Switch 2 system settings.

## Install

Install `uv` first. Prefer your OS package manager; `pip install --user uv` is a fallback.

```bash
uv venv --python 3.13
uv sync
```

`pyproject.toml` is the source of dependency and tooling configuration. `requirements.txt` is only a compatibility export.

## CLI Options

- `input`: Living the Grid JSON file.
- `--config CONFIG`: read an extra JSON config file and override values from `config.default.json`.
- `--out OUT`: output directory, defaults to `out`. Relative paths are placed under the project-level `out/` directory; for example, `--out doll` writes to `out/doll`.
- `--palette-slots N`: number of available in-game palette slots. The default is `9`.
- `--color-order frequency|original-palette|luminance|hue`: color batching and drawing order. Defaults to `original-palette`, the same order as the Living the Grid JSON / UI palette.
- `--mode safe-pixel|nearest|horizontal-runs`: drawing path mode. Defaults to `safe-pixel`.
- `--split-lines N`: maximum macro lines per part file.
- `--calibrate-only`: generate calibration scripts only.
- `--clean-output`: delete all generated files under the project `out/` directory and exit.
- `--clean-cache`: delete local Python/tool caches such as `.ruff_cache` and `__pycache__`; can be combined with `--clean-output`.
- `--preview-only`: export only `preview_quantized.png` from the JSON for quick verification; no macro parts are generated.

## Common Commands

Generate macros from Living the Grid JSON:

```bash
uv run python tomodachi_macrogen.py input.json --out doll --split-lines 8000 --mode safe-pixel
```

Generate calibration macros only:

```bash
uv run python tomodachi_macrogen.py --out calibration --calibrate-only
```

Clean all outputs:

```bash
uv run python tomodachi_macrogen.py --clean-output
```

Clean outputs and caches together:

```bash
uv run python tomodachi_macrogen.py --clean-output --clean-cache
```

Export preview only:

```bash
uv run python tomodachi_macrogen.py tests/fixtures/example.json --out preview_check --preview-only
```

Installed command entry point:

```bash
uv run tomodachi-macrogen input.json --out doll
```

## Input JSON

The JSON must include:

- `source: "living-the-grid.com"`
- `width`
- `height`
- `brush`
- `canvas`
- `palette`
- `pixels`

Each `palette[]` entry must include:

- `hex`
- `rgb`
- `press.h`
- `press.s`
- `press.b`

This tool uses `press.h/s/b` directly. It does not convert RGB through standard HSV for JSON input.

The default color order uses the original `palette[]` order, matching the swatch order shown in the Living the Grid UI.

## Output Files

JSON input mode generates:

- `image_part1.txt`, `image_part2.txt`, and so on.
- `preview_quantized.png`: preview reconstructed from JSON palette and pixels.
- `palette_report.csv`: color, HSV, Living the Grid press counts, pixel count, batch, and slot assignment report.
- `manifest.json`: summary of the generation run.
- `README_RUN.md`: hardware and in-game setup notes before running the scripts.
- `config_used.json`: the actual config after merging defaults, user config, and CLI overrides.

Calibration mode generates:

- `calibration_part1.txt`, `calibration_part2.txt`, and so on.
- `manifest.json`
- `README_RUN.md`
- `config_used.json`

Select and run the generated `.txt` files in GLaMS in numeric order.

## In-Game Setup

Before running generated scripts:

1. Enter the Tomodachi Life face paint drawing screen.
2. Select the thinnest square pixel brush.
3. Press `Y` to open the color sidebar / palette.
4. Select white or the tutorial's initial color.
5. Press the controller R shoulder button to open the full HSB picker.
6. Reset the picker before running: hold ZL until the Hue cursor is fully left.
7. Hold D-pad left + down until the color pad cursor is fully bottom-left.
8. Return to the canvas.
9. Move the brush cursor to the top-left first pixel of the canvas.
10. Run the generated `.txt` macro scripts in GLaMS.

Living the Grid H/S/B meaning:

- `H`: bottom hue strip, range `0..201`, `202` total steps. Starting from the far-left default, press `ZR` to increase.
- `S`: horizontal saturation on the 2-D pad, range `0..211`, `212` total steps. Starting from bottom-left, press D-pad right to increase.
- `B`: vertical brightness on the 2-D pad, range `0..110`, `111` total steps. Starting from bottom-left, press D-pad up to increase.

This tool uses `press.h/s/b` from the JSON directly. It does not convert RGB through standard HSV.

## Config

Defaults live in `config.default.json`. You can pass your own config file per run:

```bash
uv run python tomodachi_macrogen.py input.json --config my_config.json --out doll
```

If colors are inaccurate, tune:

- `anchor_colour_rect_method`
- `hue_slider_steps`: only affects legacy RGB->HSV calibration colors; JSON input uses `press.h` directly.
- `colour_rect_width` / `colour_rect_height`: JSON input does not use these to compute colors; they are used only for `anchor_colour_rect_method=dpad_steps` or calibration mode.
- `timing.colour_rect_anchor_hold_frames`
- `timing.colour_rect_anchor_settle_frames`
- `timing.hue_anchor_hold_frames`
- `timing.hue_step_hold_frames`
- `timing.colour_rect_step_hold_frames`
- `timing.menu_open_frames`

If drawing position drifts or inputs are missed, tune:

- `canvas_origin_x`
- `canvas_origin_y`
- `timing.movement_hold_frames`
- `timing.movement_release_frames`
- `timing.draw_hold_frames`
- `timing.draw_release_frames`

## GLaMS/SwiCC Button Names

- `A/B/X/Y`: face buttons.
- `U/D/L/R`: D-pad up/down/left/right.
- `L1/R1`: L/R shoulder buttons.
- `L2/R2`: ZL/ZR triggers.

Important: in GLaMS, `R` means D-pad right, not the R shoulder button. The R shoulder button must be written as `R1`; ZL/ZR must be written as `L2/R2`.

## Drawing Modes

- `safe-pixel`: default mode. Slowest but most reliable. Moves the cursor and taps `A` once per pixel.
- `nearest`: uses a nearest-neighbor path for small point sets; falls back to safe ordering for large sets.
- `horizontal-runs`: orders horizontal contiguous runs together, but still draws with safe per-pixel taps.

Use `safe-pixel` until real hardware timing has been calibrated.

## Development And Verification

```bash
uv sync --group dev
uv run ruff check .
uv run python -m unittest discover -s tests
```
