# tomodachi-macrogen

Convert [Living the Grid](https://living-the-grid.com/) JSON exports into SwiCC `.txt`
macros for Tomodachi Life face paint automation.

中文文档见 [README-zh.md](README-zh.md)。Changelog: [CHANGELOG.md](CHANGELOG.md).

## Download

Portable GUI builds are published on the
[GitHub Releases page](https://github.com/txfs19260817/tomodachi-macrogen/releases).
Download the latest asset for your platform, extract it, then run:

- Windows: `tomodachi-gui/tomodachi-gui.exe`
- macOS: `tomodachi-gui.app`
- Linux: `tomodachi-gui/tomodachi-gui`

No installer is produced. The artifacts are unsigned, so Windows/macOS may show the
usual first-run warning.

## Basic Workflow

1. Upload an image to Living the Grid.
2. Select `square`, `smooth`, one of `1px / 3px / 7px / 13px / 19px / 27px`, and the `game` palette.
3. Set `max colours`, for example `12`.
4. Export `JSON (per-pixel data)`.
5. Open `tomodachi-gui`, choose the JSON, and generate macros.
6. Pick the serial port, pair the controller if needed, then start drawing.

![Tomodachi Macrogen GUI screenshot](docs/gui-screenshot.png)

## In-Game Checklist

Before running generated files:

1. Open the Tomodachi Life face paint drawing screen.
2. Reset the in-game brush to `1 px`.
3. For 84-color mode, confirm the 84-color palette starts on the lower-left black swatch (`R7C1`). For full-color / HSB mode, the brush reset is enough.
4. Run generated `color_*.txt` files in filename order.
5. Do not manually change the selected palette swatch between generated files.

For non-84-color output, you may uncheck generated files in the GUI to skip colors you
already filled manually, such as a background color. 84-color output cannot skip files
because palette navigation depends on the previous selected color.

Each `color_*.txt` starts by hard-resetting the brush cursor to the canvas start. If
the JSON colors include 84-color palette coordinates, the macro opens the 84-color
Game Palette with `Y Y L1` and moves from the lower-left black swatch or the previous
84-color position. Other colors use the HSB picker with JSON `press.h/s/b` values.

## Hardware Setup

Firmware:

- SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040/releases>
- UART bridge: <https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>

To flash UF2, hold `BOOTSEL` while plugging USB, then copy the matching `.uf2` to the
`RPI-RP2` drive. Enable Pro Controller Wired Communication in Switch system settings.

- Board A plugs into the Switch / Dock and runs the SwiCC_RP2040 main firmware.
- Board B plugs into the computer and runs `SwiCC_UART_Bridge.uf2`.
- Board A GPIO0/TX connects to Board B GPIO1/RX.
- Board A GPIO1/RX connects to Board B GPIO0/TX.
- Board A GND connects to Board B GND.
- Do not connect 5V or 3V3 between boards.
- For Waveshare RP2040-Zero, wire by GPIO labels, not guessed physical position.

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

## Outputs

Generated output is written to `out/<input-name>-<timestamp>/`.

- `color_XX_*.txt`: one macro per used color, in the order they should run.
- `preview_quantized.png`: preview reconstructed from JSON.
- `reconstructed_from_macro.png`: image reconstructed from generated draw coordinates.
- `palette_report.csv`: colors, H/S/B values, pixel counts, and slot assignment.
- `manifest.json`: generation summary.
- `config_used.json`: merged runtime config.
- `README_RUN.md` / `README_RUN-en.md`: run instructions.

## CLI

The GUI is recommended for normal use. The CLI is useful for automation or manual SwiCC
file transfer.

Common commands:

```bash
# List serial ports
uv run tomodachi-macrogen --list-ports

# Generate, pair the controller, then draw
uv run tomodachi-macrogen input.json --port COM5

# Only pair the controller
uv run tomodachi-macrogen --port COM5 --match-controller

# Generate files for later use
uv run tomodachi-macrogen input.json

# Clean generated outputs and caches
uv run tomodachi-clean
```

Options:

- `input`: Living the Grid JSON.
- `--port COM5`: generate, pair, and draw through the selected serial port.
- `--list-ports`: list available serial ports.
- `--match-controller`: with no input, run the controller pairing step by itself.
- `--config CONFIG`: extra config JSON overriding `config.default.json`.
- `--color-order frequency|original-palette|luminance|hue`: color file order, default `original-palette`.
- `--diagonal-movement`: experimental D-pad diagonal movement for canvas travel.
- `--clean-output`: delete generated outputs under `out/`.
- `--clean-cache`: delete `.ruff_cache`, `__pycache__`, and similar caches.

When sending generated files manually, delete unwanted `color_*.txt` files to skip
non-84-color colors you already filled. Do not delete or skip files for 84-color output.

For each color, the generator dry-runs nearest-run, row-snake, and bounded TSP/2-opt
drawing paths, then writes the fastest one.

## Config

Defaults live in `config.default.json`. Current defaults are conservative to avoid
missed inputs on hardware.

Common tuning fields:

- `timing.*`: button, movement, and menu waits.
- `game_palette_*`: Game Palette navigation dimensions and timing.
- `movement_chunk_size` / `movement_chunk_settle_frames`: pauses during long movement.
- `enable_diagonal_movement`: experimental combined D-pad movement; leave off unless it is stable on your hardware.
- `path_tsp_max_runs`: maximum horizontal runs for the bounded TSP/2-opt candidate.
- `canvas_reset_right_steps` / `canvas_reset_down_steps`: recovery steps after the `color_*.txt` hard reset.
- `timing.canvas_reset_*`: stick hold and settle timing for the `color_*.txt` hard reset.

## Developer Setup

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

Benchmarks:

```bash
uv sync --group benchmark
uv run --group benchmark pytest benchmarks --benchmark-only
uv run --group benchmark pytest benchmarks/test_planner_strategy_benchmark.py --benchmark-only
uv run --group benchmark pytest benchmarks/test_tsp_limit_benchmark.py --benchmark-only
```

## Build Portable GUI Locally

```bash
uv sync --group build
uv run --group build tomodachi-build-gui
```

Build output goes to `dist/tomodachi-gui/` on Windows/Linux and
`dist/tomodachi-gui.app` on macOS. `tomodachi-build-gui` removes PyInstaller
intermediates by default; pass `--keep-build` if you need `build/` and
`tomodachi-gui.spec` for debugging.

GitHub Actions workflow `.github/workflows/python-app.yml` builds portable native GUI
archives on Windows, macOS, and Linux. Run it manually from Actions, or push a
semantic-version tag such as `vX.Y.Z`.

## Git Workflow

Commit messages are checked with Commitizen and should use Conventional Commits.
Enable the repository git hooks once:

```bash
git config core.hooksPath .githooks
```

Examples: `feat: add GUI color swatch`, `fix: close run instructions dialog`,
`docs: update release notes`.

The post-commit hook regenerates `CHANGELOG.md` with git-cliff and amends it into
the same commit. After each commit, check the working tree before pushing; generated
inputs such as `mmx.json` should stay untracked unless they are intentionally added as
fixtures.

```bash
# Commit local changes
git status --short
git add <files-you-intend-to-commit>
git commit -m "fix: describe the behavior"
git status --short

# Push the current branch
git push origin main

# Push an existing tag only
git push origin <tag>
```

For a patch release:

```bash
uv run --group dev cz bump --increment PATCH --yes
uv run tomodachi-check-version --tag <tag>
git push origin main <tag>
```

If `uv.lock` changes after the bump commit, amend it into that release commit and move
the local tag before pushing:

```bash
git add uv.lock
git commit --amend --no-edit
git tag -f <tag>
uv run tomodachi-check-version --tag <tag>
git push origin main <tag>
```

Preview unreleased changelog content without writing the file:

```bash
uv run --group dev git-cliff --config pyproject.toml --unreleased
```

Tag releases are checked by CI: `vX.Y.Z` must match `pyproject.toml`, then GitHub
Actions publishes the portable archives as Release assets.

## References

- Living the Grid: <https://living-the-grid.com/>
- SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040>
- Waveshare RP2040-Zero pinout: <https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg>
- TomodachiDraw picker navigation reference: <https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/CanvasNavigatorService.cs>
