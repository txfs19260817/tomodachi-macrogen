# 运行生成的 SwiCC 脚本

## 入口

通常不需要手动运行本目录里的 `.txt`。主命令会在生成后直接匹配手柄并发送：

```bash
uv run tomodachi-macrogen input.json --port COM5 --split-by-color
```

## 配对手柄

主命令会先发送这段配对输入：

```text
{A} 10
{} 60
{L1 R1} 10
{} 30
{A} 10
{} 10
```

如果同一条命令里还提供了绘图文件，会在配对输入后等待 4 秒再继续发送。

## 游戏内准备

1. 进入 face paint 绘制界面。
2. 选择与本次 Living the Grid JSON 一致的方形 smooth 笔刷大小。
3. 普通 `image_part*.txt` 需要先把画笔移动到画布左上角第一个像素。
4. 不要手动切换当前色板格，特别是运行 `color_*.txt` 时。

如果 JSON 里所有用到的颜色都有默认 84 色盘坐标，宏会用 `Y Y L1` 进入 84 色 Game Palette 并按坐标选色。否则宏会打开 HSB 选色器、复位 Hue 和颜色方块，再设置颜色。`color_*.txt` 开头会硬复位到画布左上，不在结尾主动回归。

## 运行文件

- 普通输出：按顺序运行 `image_part1.txt`、`image_part2.txt`。
- 按颜色输出：按顺序运行 `color_01_*.txt`、`color_02_*.txt`。

不要跳过或打乱顺序。

## 硬件

固件：

- SwiCC_RP2040：<https://github.com/knflrpn/SwiCC_RP2040/releases>
- UART bridge：<https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>

烧录 UF2：按住 `BOOTSEL` 插 USB，出现 `RPI-RP2` U 盘后复制对应 `.uf2`。

Switch 系统设置里需要打开 Pro Controller Wired Communication。

- A 板插 Switch / Dock，烧录 SwiCC_RP2040 主固件。
- B 板插电脑，烧录 `SwiCC_UART_Bridge.uf2`。
- A GPIO0/TX 接 B GPIO1/RX。
- A GPIO1/RX 接 B GPIO0/TX。
- A GND 接 B GND。
- 不要连接 5V 或 3V3。
- Waveshare RP2040-Zero 按 GPIO 标号接线。

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

## 参考链接

- Living the Grid：<https://living-the-grid.com/>
- SwiCC_RP2040：<https://github.com/knflrpn/SwiCC_RP2040>
- Waveshare RP2040-Zero pinout：<https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg>
