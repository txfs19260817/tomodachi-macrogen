# Running Generated GLaMS/SwiCC Scripts

## Entry Point

Open `external/GLaMS/macros.html` in Chrome or Edge.

- Right-side `commands`: paste generated `.txt` content and click `Run`.
- Left-side `recorded-inputs`: recording output, not for running macros.
- `vsync-delay`: keep the default `-1` first.

You can also bypass the web page and send over serial directly:

```bash
uv run python swicc_runner.py out/<name>/color_*.txt --port COM5 --match-controller
```

## Pair Controller

Run this in `commands` first:

```text
{A} 10
{} 60
{L1 R1} 10
{} 30
{A} 10
{} 10
```

Continue only after the Switch recognizes and responds to the controller.

## In-Game Setup

1. Open the face paint drawing screen.
2. Select the thinnest square pixel brush.
3. For normal `image_part*.txt`, move the brush cursor to the top-left first pixel first.
4. Do not manually change the selected palette swatch, especially when running `color_*.txt`.

The macro opens the palette, enters the HSB picker, resets Hue and the color pad, then sets the color. Each `color_*.txt` starts with a hard canvas reset and does not actively return at the end.

## Run Files

- Normal output: run `image_part1.txt`, `image_part2.txt`, and so on.
- Color split output: run `color_01_*.txt`, `color_02_*.txt`, and so on.

Do not skip or reorder files. Wait for one part to finish before pasting the next part.

## Hardware

- Board A plugs into Switch / Dock and runs the SwiCC_RP2040 main firmware.
- Board B plugs into the computer and runs `SwiCC_UART_Bridge.uf2`.
- Board A GPIO0/TX connects to Board B GPIO1/RX.
- Board A GPIO1/RX connects to Board B GPIO0/TX.
- Board A GND connects to Board B GND.
- Do not connect 5V or 3V3.
- For Waveshare RP2040-Zero, wire by GPIO labels.

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

GLaMS: <https://github.com/knflrpn/GLaMS>

SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040>
