# Running Generated SwiCC Scripts

## Entry Point

Use `swicc_runner.py` to send generated `.txt` files over serial:

```bash
uv run python swicc_runner.py out/<name>/color_*.txt --port COM5 --match-controller
```

## Pair Controller

`--match-controller` sends this pairing input first:

```text
{A} 10
{} 60
{L1 R1} 10
{} 30
{A} 10
{} 10
```

When drawing files are provided in the same command, the runner waits 4 seconds after pairing before sending them.

## In-Game Setup

1. Open the face paint drawing screen.
2. Select the same square smooth brush size used in the Living the Grid JSON.
3. For normal `image_part*.txt`, move the brush cursor to the top-left first pixel first.
4. Do not manually change the selected palette swatch, especially when running `color_*.txt`.

If every used JSON color includes default 84-color Game Palette coordinates, the macro stays on the Game Palette and selects colors by coordinates. Otherwise it opens the HSB picker, resets Hue and the color pad, then sets each color. Each `color_*.txt` starts with a hard canvas reset and does not actively return at the end.

## Run Files

- Normal output: run `image_part1.txt`, `image_part2.txt`, and so on.
- Color split output: run `color_01_*.txt`, `color_02_*.txt`, and so on.

Do not skip or reorder files. When using a glob, the runner sends files in natural filename order.

## Hardware

Firmware:

- SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040/releases>
- UART bridge: <https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>

To flash UF2, hold `BOOTSEL` while plugging USB, then copy the matching `.uf2` to the `RPI-RP2` drive.

Enable Pro Controller Wired Communication in Switch system settings.

- Board A plugs into Switch / Dock and runs the SwiCC_RP2040 main firmware.
- Board B plugs into the computer and runs `SwiCC_UART_Bridge.uf2`.
- Board A GPIO0/TX connects to Board B GPIO1/RX.
- Board A GPIO1/RX connects to Board B GPIO0/TX.
- Board A GND connects to Board B GND.
- Do not connect 5V or 3V3.
- For Waveshare RP2040-Zero, wire by GPIO labels.

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

## References

- Living the Grid: <https://living-the-grid.com/>
- SwiCC_RP2040: <https://github.com/knflrpn/SwiCC_RP2040>
- Waveshare RP2040-Zero pinout: <https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg>
