# 运行生成的 GLaMS/SwiCC 脚本

## RP2040 设置

- A 板插入 Switch 或 Switch 2 Dock，烧录 SwiCC_RP2040 主固件，表现为 Switch Pro Controller。
- B 板插入电脑 USB，烧录 `SwiCC_UART_Bridge.uf2`，作为 USB-UART bridge。
- A 板 GPIO0/TX 接 B 板 GPIO1/RX。
- A 板 GPIO1/RX 接 B 板 GPIO0/TX。
- A 板 GND 接 B 板 GND。
- 不要连接两块板之间的 5V 或 3V3。

在 Switch / Switch 2 系统设置里打开 Pro Controller Wired Communication。

## 游戏内准备

1. 进入 Tomodachi Life 的 face paint / 面部彩绘绘制界面。
2. 选择最细的方形像素笔刷。
3. 按 `Y` 打开颜色侧边栏。
4. 选择白色或教程要求的初始颜色。
5. 按手柄 R 肩键打开完整 HSB 选色器。
6. 运行前先重置选色器：按住 `ZL`，直到 Hue 光标完全到最左侧。
7. 按住 D-pad left + down，直到颜色方块光标完全到 bottom-left。
8. 回到画布。
9. 把画笔光标移动到画布左上角第一个像素。

## GLaMS 使用

GLaMS 仓库：<https://github.com/knflrpn/GLaMS>

如果你在本仓库里使用本地 GLaMS submodule，可以用 Chrome 或 Edge 打开 `external/GLaMS/macros.html`。

1. 打开 GLaMS 的 macros 页面。
2. 选择连接到电脑的串口，也就是烧录 `SwiCC_UART_Bridge.uf2` 的 B 板。
3. 按文件编号顺序选择生成的 `.txt` 文件，例如 `image_part1.txt`、`image_part2.txt`。
4. 先运行 `image_part1.txt`，等它结束后再运行下一个 part。
5. 如果是校准输出，则按顺序运行 `calibration_part1.txt` 等文件。

不要跳过或打乱 part 顺序；脚本会假设前一个 part 已经正确执行完成。

## Living the Grid 按键次数

对于 Living the Grid JSON 输入，颜色来自 JSON 里的按键次数：

- `H`：从 Hue 色相条最左侧默认位置开始，按 `ZR` 的次数。
- `S`：从 2D 颜色方块 bottom-left 开始，按 D-pad right 的次数。
- `B`：从 2D 颜色方块 bottom-left 开始，按 D-pad up 的次数。

如果颜色不准，优先调整：

- `anchor_colour_rect_method`
- `colour_rect_anchor_hold_frames`
- `hue_step_hold_frames`
- `colour_rect_step_hold_frames`
- `menu_open_frames`

如果绘制位置漂移或偏移，优先调整：

- `canvas_origin_x`
- `canvas_origin_y`
- `movement_hold_frames`
- `movement_release_frames`
