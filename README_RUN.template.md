# 运行生成的 SwiCC 脚本

## 入口

用 `swicc_runner.py` 通过串口发送本工具生成的 `.txt`：

```bash
uv run python swicc_runner.py out/<name>/color_*.txt --port COM5 --match-controller
```

## 配对手柄

`--match-controller` 会先发送这段配对输入：

```text
{A} 10
{} 60
{L1 R1} 10
{} 30
{A} 10
{} 10
```

如果 Switch 能识别并响应，再继续发送绘图文件。

## 游戏内准备

1. 进入 face paint 绘制界面。
2. 选择最细方形像素笔刷。
3. 普通 `image_part*.txt` 需要先把画笔移动到画布左上角第一个像素。
4. 不要手动切换当前色板格，特别是运行 `color_*.txt` 时。

宏会自己打开色板、进入 HSB 选色器、复位 Hue 和颜色方块，再设置颜色。`color_*.txt` 开头会硬复位到画布左上，不在结尾主动回归。

## 运行文件

- 普通输出：按顺序运行 `image_part1.txt`、`image_part2.txt`。
- 按颜色输出：按顺序运行 `color_01_*.txt`、`color_02_*.txt`。

不要跳过或打乱顺序。使用 glob 时，runner 会按文件名自然排序发送。

## 硬件

- A 板插 Switch / Dock，烧录 SwiCC_RP2040 主固件。
- B 板插电脑，烧录 `SwiCC_UART_Bridge.uf2`。
- A GPIO0/TX 接 B GPIO1/RX。
- A GPIO1/RX 接 B GPIO0/TX。
- A GND 接 B GND。
- 不要连接 5V 或 3V3。
- Waveshare RP2040-Zero 按 GPIO 标号接线。

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

SwiCC_RP2040：<https://github.com/knflrpn/SwiCC_RP2040>
