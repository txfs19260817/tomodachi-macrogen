# Running Generated Scripts

## First Use

1. Flash board A with the SwiCC_RP2040 main firmware: <https://github.com/knflrpn/SwiCC_RP2040/releases>
2. Flash board B with the UART bridge: <https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>
3. Wire A GPIO0/TX to B GPIO1/RX, A GPIO1/RX to B GPIO0/TX, and A GND to B GND. Do not connect 5V or 3V3.
4. Enable Pro Controller Wired Communication in Switch system settings.
5. Open Tomodachi Life's face paint drawing screen and select the same square smooth brush size used by the Living the Grid JSON.
6. In the GUI, choose the JSON, generate macros, select the serial port, then pair the controller or start drawing directly.

## Every Later Run

1. Open the same face paint drawing screen and confirm the brush size matches the current JSON.
2. For normal `image_part*.txt` output, move the brush cursor to the top-left first pixel first; `color_*.txt` starts with an automatic hard reset.
3. Do not manually change the selected palette swatch, especially when running `color_*.txt`.
4. In the GUI, click Start Drawing, or send this folder's `image_part*.txt` / `color_*.txt` files in order.
5. Run color-split `color_*.txt` files in file order; when resuming from the middle, first confirm the in-game 84-color palette is still on the color selected by the previous color file.

If JSON colors include default 84-color palette coordinates, the macro enters the 84-color Game Palette with `Y Y L1`, then moves relative to the lower-left black swatch or the last selected 84-color position. Other colors use the HSB picker with JSON `press.h/s/b` values.
