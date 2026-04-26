# tomodachi-macrogen

用于 Tomodachi Life / Tomodachi Life: Living the Dream 面部彩绘自动绘制的 PC 端 Python 3.13+ 宏脚本生成器。

本工具现在只接受 [Living the Grid](https://living-the-grid.com/) 导出的 JSON。图片量化、游戏调色盘匹配和 H/S/B 按键次数由 Living the Grid 完成；本工具负责把 JSON 转成 GLaMS/SwiCC 可运行的 `.txt` 宏脚本。

这样做的原因很直接：Living the Grid 的 `game` palette 和 H/S/B press counts 已经匹配游戏内非线性选色器，比本地重新量化和普通 HSV 换算可靠。

## 推荐流程

1. 打开 <https://living-the-grid.com/>。
2. 上传图片。
3. 选择 `square`。
4. 选择 `smooth`。
5. 选择 `1px`。
6. 设置 `max colours = 12` 或你想要的颜色数。
7. 选择 `game` palette。
8. 导出 `JSON (per-pixel data)`。
9. 用本工具把 JSON 转成 GLaMS/SwiCC 宏。

示例：

```bash
uv run python tomodachi_macrogen.py C:\Users\duola\Downloads\living-the-grid-1777233657767.json --out doll
```

相对输出会写入项目根目录的 `out/` 下，所以这里实际输出为：

```text
out/doll
```

## 硬件工作流

- A 板：插入 Switch 或 Switch 2 Dock，烧录 SwiCC_RP2040 主固件，伪装成 Switch Pro Controller。
- B 板：插入电脑 USB，烧录 `SwiCC_UART_Bridge.uf2`，作为 USB-UART bridge。
- A 板 GPIO0/TX 接 B 板 GPIO1/RX。
- A 板 GPIO1/RX 接 B 板 GPIO0/TX。
- A 板 GND 接 B 板 GND。
- 不要连接两块板之间的 5V 或 3V3。

Switch / Switch 2 系统设置里需要打开 Pro Controller Wired Communication。

## 安装

先安装 `uv`。优先使用系统包管理器；如果没有，也可以用 `pip install --user uv`。

```bash
uv venv --python 3.13
uv sync
```

`pyproject.toml` 是依赖和工具配置的来源；`requirements.txt` 只是兼容导出文件。

## CLI 参数

- `input`：Living the Grid 导出的 JSON 文件。
- `--config CONFIG`：读取额外配置 JSON，并覆盖 `config.default.json`。
- `--out OUT`：输出目录，默认是 `out`。相对路径会统一放到项目根目录的 `out/` 下；例如 `--out doll` 实际写入 `out/doll`。
- `--palette-slots N`：游戏内可用调色盘 slot 数，默认是 `9`。
- `--color-order frequency|original-palette|luminance|hue`：颜色分批和绘制顺序，默认 `original-palette`，也就是 Living the Grid JSON / UI 的调色板顺序。
- `--mode safe-pixel|nearest|horizontal-runs`：绘图路径模式，默认 `safe-pixel`。
- `--split-lines N`：每个 part 文件最多多少行。
- `--calibrate-only`：只生成校准脚本。
- `--clean-output`：删除项目根目录 `out/` 下的所有生成输出，然后退出。
- `--clean-cache`：删除本地 Python/工具缓存，例如 `.ruff_cache` 和 `__pycache__`，可以和 `--clean-output` 一起使用。
- `--preview-only`：只从 JSON 导出 `preview_quantized.png`，用于快速检查 Living the Grid 导出结果，不生成宏脚本。

## 常用命令

从 Living the Grid JSON 生成宏：

```bash
uv run python tomodachi_macrogen.py input.json --out doll --split-lines 8000 --mode safe-pixel
```

只生成校准宏：

```bash
uv run python tomodachi_macrogen.py --out calibration --calibrate-only
```

清理所有输出：

```bash
uv run python tomodachi_macrogen.py --clean-output
```

同时清理输出和缓存：

```bash
uv run python tomodachi_macrogen.py --clean-output --clean-cache
```

只导出预览图：

```bash
uv run python tomodachi_macrogen.py tests/fixtures/example.json --out preview_check --preview-only
```

也可以使用安装后的命令入口：

```bash
uv run tomodachi-macrogen input.json --out doll
```

## 输入 JSON

支持 Living the Grid v1/v2 风格 JSON，必须包含：

- `source: "living-the-grid.com"`
- `width`
- `height`
- `brush`
- `canvas`
- `palette`
- `pixels`

其中 `palette[]` 需要包含：

- `hex`
- `rgb`
- `press.h`
- `press.s`
- `press.b`

本工具会直接使用 `press.h/s/b` 设置游戏内颜色，不再把 RGB 转普通 HSV。

默认颜色顺序使用 `palette[]` 的原始顺序，这和 Living the Grid UI 里显示的 swatch 顺序一致。

## 输出文件

普通 JSON 输入会生成：

- `image_part1.txt`、`image_part2.txt` 等宏脚本。
- `preview_quantized.png`：按 JSON palette 和 pixels 还原的预览图。
- `palette_report.csv`：颜色、HSV、Living the Grid press counts、像素数量、batch 和 slot 分配报告。
- `manifest.json`：本次生成摘要。
- `README_RUN.md`：运行脚本前的硬件和游戏内设置说明。
- `config_used.json`：合并默认配置、用户配置和 CLI 参数后的实际配置。

校准模式会生成：

- `calibration_part1.txt`、`calibration_part2.txt` 等校准宏脚本。
- `manifest.json`
- `README_RUN.md`
- `config_used.json`

在 GLaMS 中按文件编号顺序选择并运行这些 `.txt` 文件。

## 游戏内准备

运行生成脚本前，手动完成以下步骤：

1. 进入 Tomodachi Life 的 face paint / 面部彩绘绘制界面。
2. 选择最细的方形像素笔刷。
3. 按 `Y` 打开颜色侧边栏 / 色板。
4. 选择白色或教程指定的初始颜色。
5. 按手柄 R 肩键进入完整 HSB 选色界面。
6. 运行前先重置选色器：按住 ZL，直到 Hue 光标完全到最左侧。
7. 按住 D-pad left + down，直到颜色方块光标完全到 bottom-left。
8. 回到画布。
9. 把画笔光标移动到画布左上角第一个像素位置。
10. 在 GLaMS 中运行生成的 `.txt` 宏脚本。

Living the Grid 的 H/S/B 含义：

- `H`：Hue 底部色相条，范围 `0..201`，共 `202` 步。从最左侧默认位置开始，按 `ZR` 向右增加。
- `S`：颜色方块横向饱和度，范围 `0..211`，共 `212` 步。从 bottom-left 开始，按 D-pad right 增加。
- `B`：颜色方块纵向亮度，范围 `0..110`，共 `111` 步。从 bottom-left 开始，按 D-pad up 增加。

本工具直接使用 JSON 里的 `press.h/s/b`，不会把 RGB 再转普通 HSV。

## 配置

默认配置在 `config.default.json`。每次运行也可以传入自己的配置文件：

```bash
uv run python tomodachi_macrogen.py input.json --config my_config.json --out doll
```

颜色如果不准，优先调整：

- `anchor_colour_rect_method`
- `hue_slider_steps`：只影响校准模式里的旧 RGB->HSV 校准色；JSON 主流程直接使用 `press.h`。
- `colour_rect_width` / `colour_rect_height`：JSON 主流程不靠它们算颜色，只在 `anchor_colour_rect_method=dpad_steps` 或校准模式中使用。
- `timing.colour_rect_anchor_hold_frames`
- `timing.colour_rect_anchor_settle_frames`
- `timing.hue_anchor_hold_frames`
- `timing.hue_step_hold_frames`
- `timing.colour_rect_step_hold_frames`
- `timing.menu_open_frames`

如果绘制位置偏移或漏步，优先调整：

- `canvas_origin_x`
- `canvas_origin_y`
- `timing.movement_hold_frames`
- `timing.movement_release_frames`
- `timing.draw_hold_frames`
- `timing.draw_release_frames`

## GLaMS/SwiCC 按键命名

生成脚本使用 GLaMS/SwiCC 风格按键名：

- `A/B/X/Y`：面板按钮。
- `U/D/L/R`：D-pad 上下左右。
- `L1/R1`：L/R 肩键。
- `L2/R2`：ZL/ZR 扳机。

注意：GLaMS 里的 `R` 是 D-pad right，不是肩键 R。肩键 R 必须写成 `R1`，ZL/ZR 必须写成 `L2/R2`。

## 绘图模式

- `safe-pixel`：默认模式，最慢但最稳。每个像素都移动光标并按一次 `A`。
- `nearest`：小规模点集会使用最近邻路径；大点集回退到安全顺序。
- `horizontal-runs`：按水平连续段排序，但仍然用逐像素安全点击绘制。

实机校准完成前建议使用 `safe-pixel`。

## 开发与验证

```bash
uv sync --group dev
uv run ruff check .
uv run python -m unittest discover -s tests
```
