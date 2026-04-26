你是资深 Python 工具链工程师、嵌入式自动化工程师、Switch 控制器输入自动化工程师。请帮我实现一个用于 Tomodachi Life / Tomodachi Life: Living the Dream 面部彩绘自动绘制的程序。

重要背景：
我使用的是旧 SwiCC_RP2040 + GLaMS 工作流，而不是让 RP2040 跑 Python。
RP2040 端已经有现成固件：
- A 板：插 Switch / Switch 2 Dock，烧 SwiCC_RP2040 主固件，伪装成 Switch Pro Controller。
- B 板：插电脑 USB，烧 SwiCC_UART_Bridge.uf2，作为 USB-UART bridge。
- A 板 GPIO0/TX 接 B 板 GPIO1/RX。
- A 板 GPIO1/RX 接 B 板 GPIO0/TX。
- A 板 GND 接 B 板 GND。
- 不要连接 5V / 3V3。
电脑端运行本程序，生成 GLaMS 可读取的 .txt 宏脚本。GLaMS 再通过串口把控制器输入发给 SwiCC_RP2040。

请不要把主要程序写成 RP2040 MicroPython 固件。
请实现 PC 端 Python 3.12+ 程序，输入图片，输出多个 GLaMS/SwiCC 可运行的 txt 脚本文件。

目标：
实现一个类似教程图里的 tomodachigif 工具：
1. 用户准备一张 256x256 的 PNG/GIF 图片。
2. 建议图片已经在 Photoshop/GIMP 中处理成 indexed color / 16 colors。
3. 程序读取图片，必要时 resize/crop/pad 到 256x256。
4. 程序量化颜色，最多 16 色，透明像素忽略或当作不绘制。
5. 程序生成多个 txt part 文件，例如：
   - image_part1.txt
   - image_part2.txt
   - image_part3.txt
6. 用户在 GLaMS 网页里选择这些 txt 文件并运行。
7. Switch 游戏内按教程图配置好画布、笔刷和初始位置后，脚本自动绘制。

必须适配这个手动配置流程：
用户会在游戏内手动完成：
1. 打开 Tomodachi Life 的面部彩绘 / face paint 绘制界面。
2. 选择最细的方形像素笔刷。
3. 按 Y 打开颜色侧边栏 / 色板。
4. 选择白色或教程指定的初始颜色。
5. 按 R 肩键切到完整选色界面 / HSB picker。
6. 确保颜色方块光标在左上角附近，Hue 色相条光标在最左侧附近。
7. 回到画布。
8. 把画笔光标移动到画布左上角第一个像素位置。
9. 然后在 GLaMS 中运行生成的 txt 文件。

程序必须假设以上初始状态是“可校准、可配置”的，不要硬编码到不可改。
请提供 config.json 或 config.toml，里面包含所有关键参数。

GLaMS/SwiCC 宏格式要求：
每一行输出一个控制器状态，格式类似：
{A} 2
{} 1
{R} 2
{} 1
{Y} 3
{} 2
{R1} 3
{} 2
{} (0 0 128 128) 120

按钮命名必须使用 GLaMS/SwiCC 风格：
- A/B/X/Y 是面板按钮。
- U/D/L/R 是 D-pad 上下左右。
- L1/R1 是 L/R 肩键。
- L2/R2 是 ZL/ZR 扳机。
- 注意：GLaMS 里的 R 是 D-pad right，不是肩键 R。
- TomodachiDraw / joycontrol 里的 r 应该映射为 GLaMS 的 R1。
- TomodachiDraw / joycontrol 里的 zl/zr 应该映射为 GLaMS 的 L2/R2。

必须实现一个宏生成层 macro_writer.py：
- tap(button, hold_frames=None, release_frames=None)
- hold(buttons, frames)
- release(frames)
- dpad(direction, steps)
- stick(lx, ly, rx, ry, frames)
- wait(frames)
- move_cursor_to(x, y)
- draw_pixel()
- split_output(max_lines_per_part, max_frames_per_part)

必须实现一个颜色选择层 color_picker.py。
请优先参考网上现成实现，尤其是 Xenthio/TomodachiDraw 的 CanvasNavigatorService.cs。
它已经包含 Tomodachi Life 2 / Switch 版完整选色器逻辑。
请在代码注释中说明参考来源。
如果无法访问网络，也请按下面算法实现，并把所有参数做成可配置。

调色盘 / 颜色切换算法要求：

1. Palette slot 数量默认 9。
   config key:
   palette_slots = 9

2. 完整选色器使用 HSB/HSV 模型。
   config key:
   color_model = "HSV"

3. Hue 色相条步数默认 200。
   config key:
   hue_slider_steps = 200

4. 颜色方块宽度默认 212 步。
   config key:
   colour_rect_width = 212

5. 颜色方块高度默认 111 步。
   config key:
   colour_rect_height = 111

6. 设置某个 palette slot 颜色的流程必须抽象成函数：
   set_palette_slot_colour(slot_index: int, rgb: tuple[int, int, int])

   伪代码：
   tap("Y")                 # 打开颜色侧边栏 / sidebar
   navigate_to_slot(slot_index)
   tap("Y")                 # 编辑当前 slot
   tap("R1")                # 注意：GLaMS/SwiCC 里肩键 R 是 R1，不是 R
   set_hue(hue_degrees)
   set_colour_rect(saturation, brightness)
   tap("A")                 # 确认颜色
   tap("B")                 # 回到画布 / ensure canvas focus

7. navigate_to_slot(slot_index):
   - 先长按 D-pad down，把选择锚定到底部 slot。
   - 总 slot 数为 9。
   - steps_up = palette_slots - 1 - slot_index。
   - 然后按 U steps_up 次。
   - 所有 hold_frames、step_frames、settle_frames 都必须可配置。

8. set_hue(hue_degrees):
   - 先长按 L2，把 hue slider 归零。
   - target_step = int(hue_degrees / 360 * hue_slider_steps)
   - 然后按 R2 target_step 次。
   - L2/R2 是 ZL/ZR，在 GLaMS/SwiCC 中不要写成 ZL/ZR。
   - 每一次 R2 press 后必须有 release frame，避免游戏只识别一次长按。

9. set_colour_rect(saturation, brightness):
   - sat_x = int(saturation * colour_rect_width)
   - bri_y = int((1 - brightness) * colour_rect_height)
   - 先把颜色方块光标锚定到左上角。
   - 默认可以用左摇杆 up-left 长按：
     {} (0 0 128 128) anchor_hold_frames
     {} (128 128 128 128) anchor_settle_frames
   - 但必须提供 fallback：
     anchor_colour_rect_method = "analog" | "dpad_hold" | "dpad_steps"
   - 然后按 D-pad R sat_x 次，按 D-pad D bri_y 次。
   - 注意这里的 R/D 是 D-pad right/down，不是肩键。

10. activate_palette_slot(slot_index):
    - tap("Y")
    - navigate_to_slot(slot_index)
    - tap("A")
    - tap("B")
    - 更新当前 active_palette_slot 状态。

11. 所有颜色选择函数必须集中在 color_picker.py，不能散落在绘图代码里。
    因为我之后可能要在游戏里实测并修改这些函数。

图片处理要求：
1. 支持 PNG/GIF/JPEG/WebP 输入。
2. 输出统一处理成 256x256。
3. 支持：
   --resize-mode stretch
   --resize-mode contain
   --resize-mode cover
   --resize-mode none
4. 支持透明像素：
   - 默认 transparent pixels = skip drawing。
   - 可选 transparent pixels = white。
5. 支持颜色量化：
   --max-colors 16
   --max-colors 9
   --dither none|floyd-steinberg
6. 输出 preview_quantized.png。
7. 输出 palette_report.csv，包含：
   - color_index
   - rgb
   - hsv
   - pixel_count
   - assigned_slot
   - batch_index

调色盘 slot / 颜色批次要求：
TomodachiDraw 参考实现似乎有 9 个 palette slots。
但教程图里建议导出 indexed gif 16 色。
所以程序必须支持 colors > palette_slots 的情况。

要求：
1. 如果颜色数 <= 9：
   - 初始化 9 个 palette slots 中需要的颜色。
   - 每种颜色绘制前 activate 对应 slot。
2. 如果颜色数 > 9：
   - 分 batch。
   - 每 batch 最多 9 个颜色。
   - 每个 batch 开始时 set_palette_slot_colour 写入这一批颜色。
   - 然后绘制这一批颜色对应的像素。
   - 输出文件可以按 batch/part 切分。
3. 颜色排序默认按 pixel_count 降序。
4. 提供可选参数：
   --color-order frequency|original-palette|luminance|hue

绘图路径要求：
先实现可靠版本，不要一开始就过度优化。
必须有 safe pixel mode：
1. 对每个颜色，收集所有属于该颜色的像素。
2. 路径可以使用蛇形扫描：
   - y 从 0 到 255
   - 偶数行 x 从 0 到 255
   - 奇数行 x 从 255 到 0
3. 跟踪当前画笔位置 current_x/current_y。
4. move_cursor_to(x, y) 使用 D-pad U/D/L/R 移动到目标坐标。
5. draw_pixel() 输出 tap("A")。
6. 移动和按键之间必须有 release/wait，避免漏输入或连发错误。

可选优化：
1. 实现 nearest-neighbor path optimization。
2. 实现 run-length horizontal strokes。
3. 实现 region/flood-fill 优化，但必须默认关闭或可配置。
4. 任何优化都必须可回退到 safe pixel mode。

输出要求：
程序运行后输出一个文件夹：
out/
  image_part1.txt
  image_part2.txt
  ...
  preview_quantized.png
  palette_report.csv
  manifest.json
  README_RUN.md
  config_used.json

README_RUN.md 必须写清楚：
1. 两块 RP2040 分别烧什么。
2. 怎么接线。
3. Switch / Switch 2 要打开 Pro Controller Wired Communication。
4. 游戏里怎么按教程图配置：
   - 进入绘图界面。
   - 选择最细方形像素笔刷。
   - 打开色板。
   - 进入完整选色界面。
   - 确保 Hue 和颜色方块光标处于已知初始位置。
   - 回画布。
   - 把画笔放到左上角第一个像素。
5. 在 GLaMS 中如何选择 txt 文件并运行。
6. 如果颜色不准，优先修改哪些 config：
   - hue_slider_steps
   - colour_rect_width
   - colour_rect_height
   - anchor_hold_frames
   - step_frames
   - menu_open_frames
7. 如果位置偏移，如何调：
   - canvas_origin_x
   - canvas_origin_y
   - step_frames
   - movement_release_frames

CLI 要求：
实现命令行接口：

python tomodachi_macrogen.py input.png --out out --max-colors 16 --palette-slots 9 --resize-mode contain --split-lines 8000 --mode safe-pixel

必须支持：
--config config.json
--out out_dir
--max-colors N
--palette-slots N
--resize-mode stretch|contain|cover|none
--dither none|floyd-steinberg
--color-order frequency|original-palette|luminance|hue
--mode safe-pixel|nearest|horizontal-runs
--split-lines N
--split-frames N
--calibrate-only
--generate-test-pattern

校准功能：
实现 --calibrate-only，生成 calibration txt：
1. 测试 Y 打开 sidebar。
2. 测试 navigate_to_slot(0..8)。
3. 测试 set_palette_slot_colour，把 9 个 slot 设置成：
   red, orange, yellow, green, cyan, blue, purple, black, white。
4. 测试 activate_palette_slot。
5. 测试在画布左上角画一个 3x3 或 8x8 色块。
这样我可以在游戏里看颜色切换是否正确。

代码结构要求：
请生成完整项目：

D:\Projects\tomodachi-macrogen (pwd)/
  tomodachi_macrogen.py
  config.default.json
  requirements.txt
  README.md
  src/
    image_loader.py
    quantize.py
    palette.py
    color_picker.py
    macro_writer.py
    path_planner.py
    glams_format.py
    splitter.py
  tests/
    test_color_conversion.py
    test_macro_writer.py
    test_palette_batching.py
    test_path_planner.py

实现要求：
1. 使用 Pillow 处理图片。
2. 使用标准库 csv/json/pathlib/argparse。
3. 每个核心函数加 type hints。
4. 不要依赖 obscure package。
5. 所有坐标和颜色转换要有单元测试。
6. 代码必须能在 Windows/macOS/Linux 运行。
7. 不要直接控制串口；本程序只生成 txt。
8. 不要要求联网运行。
9. 如果参考链接不可访问，仍然根据 prompt 中给出的算法实现。

请特别注意：
- GLaMS 的 R 是 D-pad right。
- 肩键 R 必须输出 R1。
- ZL/ZR 必须输出 L2/R2。
- 连续按 R2/L2/D-pad 步进时，每次按下后要释放，否则游戏可能只识别一次。
- 所有时序都要做成 config。
- 生成的脚本要尽量慢一点但稳定，先可靠再优化。

参考链接：
- SwiCC_RP2040:
  https://github.com/knflrpn/SwiCC_RP2040
- GLaMS:
  https://github.com/knflrpn/GLaMS
- TomodachiDraw:
  https://github.com/Xenthio/TomodachiDraw
- TomodachiDraw colour picker / CanvasNavigatorService:
  https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/CanvasNavigatorService.cs
- TomodachiDraw image processing:
  https://github.com/Xenthio/TomodachiDraw/blob/master/TomodachiDraw/Services/ImageProcessorService.cs

最终请输出：
1. 完整代码。
2. config.default.json。
3. README.md。
4. 一个示例命令。
5. 一个 calibration-only 示例。
6. 清楚说明两块 RP2040 分别烧什么固件。