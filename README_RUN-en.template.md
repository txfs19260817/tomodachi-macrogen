# Running Generated Scripts

## First Use

1. Flash board A with the SwiCC_RP2040 main firmware: <https://github.com/knflrpn/SwiCC_RP2040/releases>
2. Flash board B with the UART bridge: <https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>
3. Wire A GPIO0/TX to B GPIO1/RX, A GPIO1/RX to B GPIO0/TX, and A GND to B GND. Do not connect 5V or 3V3.
4. Enable Pro Controller Wired Communication in Switch system settings.
5. Open Tomodachi Life's face paint drawing screen and reset the brush to 1 px.
6. In the GUI, choose the JSON, generate macros, select the serial port, then pair the controller and start drawing.

## Every Later Run

1. Open the same face paint drawing screen and reset the brush to 1 px.
2. 84-color mode: confirm the 84-color palette starts on the lower-left black swatch (R7C1); full-color / HSB mode only requires the brush to be 1 px.
3. Run `color_*.txt` files in filename order. Do not manually change the selected palette swatch between files.
4. For non-84-color output, uncheck files in the GUI; when sending manually with CLI / SwiCC, delete unwanted color files first. 84-color mode cannot skip files.
5. When resuming 84-color output from the middle, first confirm the in-game palette is still on the color selected by the previous color file.
