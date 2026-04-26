# Running Generated GLaMS/SwiCC Scripts

## RP2040 setup

- Board A plugs into the Switch or Switch 2 Dock and runs the SwiCC_RP2040 main firmware.
- Board A should appear as a Switch Pro Controller.
- Board B plugs into the computer over USB and runs SwiCC_UART_Bridge.uf2 as the USB-UART bridge.
- Connect Board A GPIO0/TX to Board B GPIO1/RX.
- Connect Board A GPIO1/RX to Board B GPIO0/TX.
- Connect Board A GND to Board B GND.
- Do not connect 5V or 3V3 between the boards.

Enable Pro Controller Wired Communication in the Switch or Switch 2 system settings.

## In-game setup

1. Open the Tomodachi Life face paint drawing screen.
2. Select the thinnest square pixel brush.
3. Press Y to open the color sidebar.
4. Select white or the tutorial's required initial color.
5. Press the R shoulder button to open the full HSB picker.
6. Reset the picker before running: hold ZL until the hue cursor is fully left.
7. Hold D-pad left + down until the pad cursor is fully bottom-left.
8. Return to the canvas.
9. Move the brush cursor to the top-left first pixel of the canvas.
10. In GLaMS, choose the generated txt files in numeric order and run them.

## Living the Grid press counts

For Living the Grid JSON input, color values come from JSON press counts:

- H is ZR presses on the hue strip from the far-left default.
- S is D-pad right presses from the 2-D pad bottom-left.
- B is D-pad up presses from the 2-D pad bottom-left.

If colors are inaccurate, tune:

- anchor_colour_rect_method
- colour_rect_anchor_hold_frames
- hue_step_hold_frames
- colour_rect_step_hold_frames
- menu_open_frames

If position drifts or offsets, tune:

- canvas_origin_x
- canvas_origin_y
- movement_hold_frames
- movement_release_frames
