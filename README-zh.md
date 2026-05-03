# tomodachi-macrogen

把 [Living the Grid](https://living-the-grid.com/) 导出的 JSON 转成 SwiCC `.txt` 宏，用于 Tomodachi Life 面部彩绘自动绘制。

本项目不再处理图片输入。图片量化、调色板和 H/S/B 按键次数交给 Living the Grid；这里只负责生成可运行宏。

English documentation: [README.md](README.md).

## 下载

免安装 GUI 包发布在
[GitHub Releases 页面](https://github.com/txfs19260817/tomodachi-macrogen/releases)。
下载对应平台的最新 asset，解压后直接运行：

- Windows：`tomodachi-gui/tomodachi-gui.exe`
- macOS：`tomodachi-gui.app`
- Linux：`tomodachi-gui/tomodachi-gui`

不会生成安装器。产物未签名，Windows/macOS 首次运行时可能会有系统提示。

## GUI 流程

1. 在 Living the Grid 上传图片。
2. 选择 `square`、`smooth`、`1px / 3px / 7px / 13px / 19px / 27px` 之一、`game` palette。
3. 设置 `max colours`，例如 `12`。
4. 导出 `JSON (per-pixel data)`。
5. 打开 `tomodachi-gui`，选择 JSON，生成宏。
6. 选择串口，需要时先匹配手柄，然后开始绘画。

## 安装

```bash
uv venv --python 3.13
uv sync
```

开发检查：

```bash
uv sync --group dev --group test
uv run ruff check .
uv run pytest -n auto tests
```

## 本地构建 Portable GUI

```bash
uv sync --group build
uv run --group build python scripts/build_gui.py
```

构建结果在 Windows/Linux 上写到 `dist/tomodachi-gui/`，在 macOS 上写到
`dist/tomodachi-gui.app`。

GitHub Actions 工作流 `.github/workflows/python-app.yml` 会用 PyInstaller onedir
分别在 Windows、macOS、Linux 上构建免安装 GUI 压缩包。可以在 Actions 页面手动运行，
也可以推送 `v1.0.1` 这类语义化版本 tag 触发。

tag 发布就是版本 hook：workflow 会检查 `vX.Y.Z` 是否和 `pyproject.toml` 里的
项目版本一致，然后把 portable 压缩包发布成 GitHub Release assets。

## 原生 GUI

源码运行用 `uv run tomodachi-gui`，普通使用建议下载 Release 包。GUI 把 CLI 的流程
放到一个窗口里：选择 Living the Grid JSON、生成输出、匹配手柄、发送绘图并显示进度。
GUI 会渲染 JSON 预览图，支持中文/英文和亮色/暗色主题，串口发送在后台线程执行。

## CLI

`tomodachi-macrogen` 是主命令。提供 JSON 和 `--port` 时，它会写入带时间戳的
输出目录，发送匹配手柄宏，等待 4 秒，然后用 SwiCC `+Q` 编码和 `+GQF` 队列轮询
发送绘图宏。

不提供 `--port` 时只生成文件。不提供 JSON 且使用 `--match-controller` 时，只发送
匹配手柄宏。

常用命令：

```bash
# 查看串口
uv run tomodachi-macrogen --list-ports

# 生成、匹配手柄、开始绘画
uv run tomodachi-macrogen input.json --port COM5 --split-by-color

# 只匹配手柄，不做其它事
uv run tomodachi-macrogen --port COM5 --match-controller

# 只生成文件，不碰串口
uv run tomodachi-macrogen input.json --split-by-color

# 清理输出和缓存
uv run tomodachi-macrogen --clean-output --clean-cache
```

输出固定写入 `out/<JSON 文件名>-<时间戳>/`。

- `input`：Living the Grid JSON。
- `--port COM5`：通过指定串口生成、匹配手柄并绘画。
- `--list-ports`：列出可用串口。
- `--match-controller`：不提供 JSON 时，只发送匹配手柄宏。
- `--config CONFIG`：额外配置，会覆盖 `config.default.json`。
- `--palette-slots N`：游戏内可用色板格数，默认 `9`。
- `--color-order frequency|original-palette|luminance|hue`：颜色顺序，默认 `original-palette`，也就是 Living the Grid UI 顺序。
- `--split-lines N`：每个 part 最多多少行；`0` 表示禁用切分。
- `--split-by-color`：一个颜色一个文件，方便单独重跑某个颜色。
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

## 硬件

固件：

- SwiCC_RP2040：<https://github.com/knflrpn/SwiCC_RP2040/releases>
- UART bridge：<https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>

烧录 UF2：按住 `BOOTSEL` 插 USB，出现 `RPI-RP2` U 盘后复制对应 `.uf2`。

Switch 系统设置里需要打开 Pro Controller Wired Communication。

- A 板插 Switch / Dock，烧录 SwiCC_RP2040 主固件，表现为 Switch Pro Controller。
- B 板插电脑，烧录 `SwiCC_UART_Bridge.uf2`，作为 USB-UART bridge。
- A GPIO0/TX 接 B GPIO1/RX。
- A GPIO1/RX 接 B GPIO0/TX。
- A GND 接 B GND。
- 不要连接两块板之间的 5V 或 3V3。
- Waveshare RP2040-Zero 按 GPIO 标号接线，不要按物理位置猜。

![Waveshare RP2040-Zero pinout](https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg)

## 游戏内准备

1. 进入 face paint 绘制界面。
2. 选择与 Living the Grid JSON 一致的方形 smooth 笔刷大小。
3. 普通 `image_part*.txt` 需要先把画笔移动到画布左上角第一个像素。
4. 运行宏前不要手动改变当前色板格，特别是 `--split-by-color`。

生成的宏会把一个 Living the Grid cell 当作一个笔刷 stamp，移动距离按 `brush.px` 放大。如果每个用到的颜色都带 `game: {row, col}`、`game: {extra}` 或 `R1·C1` 这类 label，宏会留在默认 84 色盘里选色。否则会打开 H/S/B 选色器，并按 JSON 里的 `press.h/s/b` 调色。`color_*.txt` 会在开头硬复位到画布左上：左上推摇杆 7 秒，再向右 192、向下 77。

## 配置

默认配置在 `config.default.json`，当前默认值偏慢，优先保证实机不漏步。

常调字段：

- `timing.*`：按键、移动、菜单等待时间。
- `game_palette_*`：默认 Game Palette 导航尺寸和复位等待。
- `movement_chunk_size` / `movement_chunk_settle_frames`：长距离移动时分块停顿。
- `canvas_reset_right_steps` / `canvas_reset_down_steps`：`color_*.txt` 开头硬复位后的回退步数。
- `timing.canvas_reset_*`：`color_*.txt` 开头硬复位的摇杆保持和停顿时间。
- `split_lines`：默认 part 行数。

## 参考链接

- Living the Grid：<https://living-the-grid.com/>
- SwiCC_RP2040：<https://github.com/knflrpn/SwiCC_RP2040>
- Waveshare RP2040-Zero pinout：<https://mischianti.org/wp-content/uploads/2022/09/Waveshare-rp2040-zero-Raspberry-Pi-Pico-alternative-pinout.jpg>
- TomodachiDraw 选色器导航参考：<https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/CanvasNavigatorService.cs>
