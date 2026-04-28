# tomodachi-macrogen

把 [Living the Grid](https://living-the-grid.com/) 导出的 JSON 转成 SwiCC `.txt` 宏，用于 Tomodachi Life 面部彩绘自动绘制。

本项目不再处理图片输入。图片量化、调色板和 H/S/B 按键次数交给 Living the Grid；这里只负责生成可运行宏。

English documentation: [README-en.md](README-en.md).

## 流程

1. 在 Living the Grid 上传图片。
2. 选择 `square`、`smooth`、`1px`、`game` palette。
3. 设置 `max colours`，例如 `12`。
4. 导出 `JSON (per-pixel data)`。
5. 运行本工具生成 SwiCC 宏。
6. 用 `swicc_runner.py` 按顺序发送生成的 `.txt`。

```bash
uv run python tomodachi_macrogen.py input.json
```

默认输出到 `out/input/`。例如 `abc.json` 会生成到 `out/abc/`。

## 安装

```bash
uv venv --python 3.13
uv sync
```

开发检查：

```bash
uv sync --group dev
uv run ruff check .
uv run python -m unittest discover -s tests
```

## 常用命令

```bash
# 生成宏，默认每 50000 行切一个 part
uv run python tomodachi_macrogen.py input.json

# 不切分，只生成一个 image_part1.txt
uv run python tomodachi_macrogen.py input.json --split-lines 0

# 按颜色拆分，一个 txt 只画一种颜色
uv run python tomodachi_macrogen.py input.json --split-by-color

# 清理输出和缓存
uv run python tomodachi_macrogen.py --clean-output --clean-cache
```

## Python 串口发送

用 `swicc_runner.py` 通过 B 板 USB-UART 发送生成的 `.txt`：

```bash
# 查看串口
uv run python swicc_runner.py --list-ports

# 先检查文件顺序和编码预览，不碰串口
uv run python swicc_runner.py out/nkidhr/color_*.txt --dry-run

# 匹配手柄后按文件名顺序发送
uv run python swicc_runner.py out/nkidhr/color_*.txt --port COM5 --match-controller
```

这个 runner 使用 SwiCC `+Q` 编码和 `+GQF` 队列轮询发送宏。

## CLI

- `input`：Living the Grid JSON。
- `--out OUT`：输出目录；相对路径会放到项目 `out/` 下。
- `--config CONFIG`：额外配置，会覆盖 `config.default.json`。
- `--palette-slots N`：游戏内可用色板格数，默认 `9`。
- `--color-order frequency|original-palette|luminance|hue`：颜色顺序，默认 `original-palette`，也就是 Living the Grid UI 顺序。
- `--split-lines N`：每个 part 最多多少行；`0` 表示禁用切分。
- `--split-by-color`：一个颜色一个文件，方便单独重跑某个颜色。
- `--clean-output`：删除 `out/` 下的生成结果。
- `--clean-cache`：删除 `.ruff_cache`、`__pycache__` 等缓存。

绘图路径固定为同色水平连续段规划，不再暴露路径模式 flag。

## swicc_runner.py CLI

- `files`：生成的 `.txt` 文件或 glob，例如 `out/nkidhr/color_*.txt`。
- `--list-ports`：列出可用串口。
- `--port COM5`：选择 B 板 USB-UART 串口。
- `--match-controller`：发送匹配手柄宏。
- `--dry-run`：只解析和预览，不访问串口。
- `--vsync-delay N`：默认 `-1`，即禁用 VSYNC delay。

## 输出

- `image_part*.txt`：普通宏脚本。
- `color_XX_*.txt`：`--split-by-color` 模式下的单色脚本。
- `preview_quantized.png`：按 JSON 还原的预览。
- `reconstructed_from_macro.png`：按宏绘制坐标重建的图，用来检查路径计划。
- `palette_report.csv`：颜色、H/S/B、像素数和 slot 分配。
- `manifest.json`：生成摘要。
- `config_used.json`：实际使用配置。
- `README_RUN.md` / `README_RUN-en.md`：运行说明。

## 硬件

- A 板插 Switch / Dock，烧录 SwiCC_RP2040 主固件，表现为 Switch Pro Controller。
- B 板插电脑，烧录 `SwiCC_UART_Bridge.uf2`，作为 USB-UART bridge。
- A GPIO0/TX 接 B GPIO1/RX。
- A GPIO1/RX 接 B GPIO0/TX。
- A GND 接 B GND。
- 不要连接两块板之间的 5V 或 3V3。
- Waveshare RP2040-Zero 按 GPIO 标号接线，不要按物理位置猜。

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

固件：

- SwiCC_RP2040：<https://github.com/knflrpn/SwiCC_RP2040/releases>
- UART bridge：<https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>

烧录 UF2：按住 `BOOTSEL` 插 USB，出现 `RPI-RP2` U 盘后复制对应 `.uf2`。

Switch 系统设置里需要打开 Pro Controller Wired Communication。

## 游戏内准备

1. 进入 face paint 绘制界面。
2. 选择最细方形像素笔刷。
3. 普通 `image_part*.txt` 需要先把画笔移动到画布左上角第一个像素。
4. 运行宏前不要手动改变当前色板格，特别是 `--split-by-color`。

生成的宏会负责打开色板、进入完整 HSB 选色器、复位 Hue 和颜色方块，再按 JSON 里的 `press.h/s/b` 调色。`color_*.txt` 会在开头硬复位到画布左上：左上推摇杆 7 秒，再向右 192、向下 77。

## 配置

默认配置在 `config.default.json`，当前默认值偏慢，优先保证实机不漏步。

常调字段：

- `timing.*`：按键、移动、菜单等待时间。
- `movement_chunk_size` / `movement_chunk_settle_frames`：长距离移动时分块停顿。
- `canvas_reset_right_steps` / `canvas_reset_down_steps`：`color_*.txt` 开头硬复位后的回退步数。
- `timing.canvas_reset_*`：`color_*.txt` 开头硬复位的摇杆保持和停顿时间。
- `split_lines`：默认 part 行数。
