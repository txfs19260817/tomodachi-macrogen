# tomodachi-macrogen

把 [Living the Grid](https://living-the-grid.com/) 导出的 JSON 转成 GLaMS/SwiCC `.txt` 宏，用于 Tomodachi Life 面部彩绘自动绘制。

本项目不再处理图片输入。图片量化、调色板和 H/S/B 按键次数交给 Living the Grid；这里只负责生成可运行宏。

英文文档见 [README-en.md](README-en.md)。

## 流程

1. 在 Living the Grid 上传图片。
2. 选择 `square`、`smooth`、`1px`、`game` palette。
3. 设置 `max colours`，例如 `12`。
4. 导出 `JSON (per-pixel data)`。
5. 运行本工具生成 GLaMS 宏。
6. 在 GLaMS 里按顺序运行生成的 `.txt`。

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

# 只导出预览图，快速检查 JSON
uv run python tomodachi_macrogen.py input.json --preview-only

# 使用慢速实机配置
uv run python tomodachi_macrogen.py input.json --config config.slow.json

# 清理输出和缓存
uv run python tomodachi_macrogen.py --clean-output --clean-cache
```

## CLI

- `input`：Living the Grid JSON。
- `--out OUT`：输出目录；相对路径会放到项目 `out/` 下。
- `--config CONFIG`：额外配置，会覆盖 `config.default.json`。
- `--palette-slots N`：游戏内可用色板格数，默认 `9`。
- `--color-order frequency|original-palette|luminance|hue`：颜色顺序，默认 `original-palette`，也就是 Living the Grid UI 顺序。
- `--split-lines N`：每个 part 最多多少行；`0` 表示禁用切分。
- `--split-by-color`：一个颜色一个文件，方便单独重跑某个颜色。
- `--calibrate-only`：只生成校准宏。
- `--preview-only`：只生成 `preview_quantized.png`。
- `--clean-output`：删除 `out/` 下的生成结果。
- `--clean-cache`：删除 `.ruff_cache`、`__pycache__` 等缓存。

绘图路径固定为同色水平连续段规划，不再暴露路径模式 flag。

## 输出

- `image_part*.txt`：普通宏脚本。
- `color_XX_*.txt`：`--split-by-color` 模式下的单色脚本。
- `preview_quantized.png`：按 JSON 还原的预览。
- `reconstructed_from_macro.png`：按宏绘制坐标重建的图，用来检查路径计划。
- `palette_report.csv`：颜色、H/S/B、像素数和 slot 分配。
- `manifest.json`：生成摘要。
- `config_used.json`：实际使用配置。
- `README_RUN.md` / `README_RUN-en.md`：运行说明。

## GLaMS

GLaMS：<https://github.com/knflrpn/GLaMS>

本仓库把 GLaMS 放在 `external/GLaMS`：

```bash
git submodule update --init --recursive
git submodule update --remote external/GLaMS
```

使用标准页面 `external/GLaMS/macros.html`。右侧大输入框 `commands` 用来粘贴并运行本工具生成的 `.txt`；左侧 `recorded-inputs` 是录制输出，不是运行入口。

配对手柄时可先在 `commands` 运行：

```text
{A} 10
{} 60
{L1 R1} 10
{} 30
{A} 10
{} 10
```

多个 part 要按文件名顺序逐个运行。

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
3. 把画笔移动到画布左上角第一个像素。
4. 运行宏前不要手动改变当前色板格，特别是 `--split-by-color`。

生成的宏会负责打开色板、进入完整 HSB 选色器、复位 Hue 和颜色方块，再按 JSON 里的 `press.h/s/b` 调色。

## 配置

默认配置在 `config.default.json`。实机漏步或过快时先试：

```bash
uv run python tomodachi_macrogen.py input.json --config config.slow.json
```

常调字段：

- `timing.*`：按键、移动、菜单等待时间。
- `movement_chunk_size` / `movement_chunk_settle_frames`：长距离移动时分块停顿。
- `canvas_origin_x` / `canvas_origin_y`：画布起点偏移。
- `split_lines`：默认 part 行数。
