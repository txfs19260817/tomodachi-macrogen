# 运行生成的脚本

## 第一次使用

1. 给 A 板刷 SwiCC_RP2040 主固件：<https://github.com/knflrpn/SwiCC_RP2040/releases>
2. 给 B 板刷 UART bridge：<https://github.com/knflrpn/SwiCC_RP2040/blob/main/documentation/SwiCC_UART_Bridge.uf2>
3. 接线：A GPIO0/TX 到 B GPIO1/RX，A GPIO1/RX 到 B GPIO0/TX，A GND 到 B GND。不要连接 5V 或 3V3。
4. 在 Switch 系统设置里打开 Pro Controller Wired Communication。
5. 进入 Tomodachi Life 的 face paint 绘制界面，把画笔重置为 1px。
6. 在 GUI 里选择 JSON、生成宏、选择串口，然后点“匹配手柄”或直接开始绘画。

## 以后每次绘画

1. 打开同一个 face paint 绘制界面，把画笔重置为 1px。
2. 84 色模式还需要确认 84 色板起点是左下角黑色（R7C1）；全色 / HSB 模式只需要画笔是 1px。
3. 普通 `image_part*.txt` 输出需要先把画笔移动到画布左上角第一个像素；`color_*.txt` 会在开头自动硬复位。
4. 不要手动切换当前色板格，特别是运行 `color_*.txt` 时。
5. 在 GUI 里点“开始绘画”，或按顺序发送本目录里的 `image_part*.txt` / `color_*.txt`。
6. 按颜色拆分的 `color_*.txt` 需要按文件顺序运行；如果从中间恢复，先确认游戏里的 84 色板仍停在上一个颜色文件选中的颜色。

如果 JSON 颜色带默认 84 色盘坐标，宏会用 `Y Y L1` 进入 84 色 Game Palette，并从左下角黑色或上一次选中的 84 色位置相对移动；其它颜色会进入 HSB 选色器并使用 JSON 里的 `press.h/s/b`。
