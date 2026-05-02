import i18n

DEFAULT_LOCALE = "zh"
LOCALE_OPTIONS = (("zh", "中文"), ("en", "English"))

TRANSLATIONS = {
    "zh": {
        "app.title": "Tomodachi Macrogen",
        "preview.title": "JSON 预览",
        "preview.empty": "选择 Living the Grid JSON 后显示预览",
        "preview.unloaded": "未加载",
        "preview.meta": (
            "%name\n%width x %height grid, brush %{brush_px}px, "
            "%colors colors, palette %palette"
        ),
        "hero.title": "JSON → Macro → SwiCC",
        "hero.subtitle": "生成宏、匹配手柄、发送绘图都在后台执行；界面不会承载长文本。",
        "theme.label": "主题",
        "theme.light": "亮色",
        "theme.dark": "暗色",
        "language.label": "语言",
        "menu.view": "视图",
        "menu.language": "语言",
        "menu.theme": "主题",
        "generate.group": "1. 生成输出",
        "generate.input": "输入",
        "generate.output": "输出",
        "generate.input_placeholder": "Living the Grid JSON",
        "generate.choose_json": "选择 JSON",
        "generate.open_living_grid": "打开 Living the Grid",
        "generate.open_living_grid_tooltip": "在默认浏览器中打开 Living the Grid 生成 JSON。",
        "generate.output_hint": "自动写入 out/<JSON 名>-<时间戳>/",
        "generate.split_by_color": "按颜色拆分（推荐，便于中断后重跑单色）",
        "generate.button": "生成宏",
        "serial.group": "2. 串口和手柄",
        "serial.port": "串口",
        "serial.refresh": "刷新串口",
        "serial.match": "匹配手柄",
        "draw.group": "3. 绘画",
        "draw.button": "开始绘画",
        "draw.cancel": "取消",
        "draw.cancel_tooltip": "停止继续发送绘图宏；已进入 SwiCC 队列的帧可能还会执行一小段。",
        "draw.disabled_tooltip": "先生成宏，才可以开始绘画。",
        "draw.enabled_tooltip": "发送当前生成的绘图文件。",
        "draw.current_file": "当前文件：-",
        "draw.current_file_detail": "当前文件：%index / %total · %name",
        "file_dialog.json_title": "选择 Living the Grid JSON",
        "file_dialog.json_filter": "JSON 文件 (*.json)",
        "status.ready": "Ready",
        "status.generating": "Generating macros...",
        "status.loading_json": "读取 JSON...",
        "status.planning_macros": "规划宏...",
        "status.writing_output": "写入输出...",
        "status.generated": "Generated",
        "status.pairing": "Pairing controller...",
        "status.pairing_drawing": "Pairing and drawing...",
        "status.drawing": "绘画中...",
        "status.cancelling": "正在取消...",
        "status.cancelled": "已取消",
        "status.done": "Done",
        "status.failed": "Failed",
        "error.title": "Tomodachi Macrogen",
        "error.read_json": "无法读取 JSON：%error",
        "error.serial_unavailable": "串口不可用：%error",
        "error.no_json": "先选择 Living the Grid JSON。",
        "error.no_port": "先选择串口。",
        "error.no_files": "先生成宏。",
        "error.open_living_grid": "无法打开 Living the Grid。",
        "generation.meta": "%out_dir\n%files files, %lines lines, %frames frames",
        "progress.transfer": "%percent  queue=%queue  ETA %eta",
    },
    "en": {
        "app.title": "Tomodachi Macrogen",
        "preview.title": "JSON Preview",
        "preview.empty": "Choose a Living the Grid JSON to preview it",
        "preview.unloaded": "Not loaded",
        "preview.meta": (
            "%name\n%width x %height grid, brush %{brush_px}px, "
            "%colors colors, palette %palette"
        ),
        "hero.title": "JSON → Macro → SwiCC",
        "hero.subtitle": (
            "Macro generation, controller pairing, and drawing run in background workers; "
            "the UI never loads long macro text."
        ),
        "theme.label": "Theme",
        "theme.light": "Light",
        "theme.dark": "Dark",
        "language.label": "Language",
        "menu.view": "View",
        "menu.language": "Language",
        "menu.theme": "Theme",
        "generate.group": "1. Generate Output",
        "generate.input": "Input",
        "generate.output": "Output",
        "generate.input_placeholder": "Living the Grid JSON",
        "generate.choose_json": "Choose JSON",
        "generate.open_living_grid": "Open Living the Grid",
        "generate.open_living_grid_tooltip": (
            "Open Living the Grid in your default browser to create JSON."
        ),
        "generate.output_hint": "Automatically writes to out/<JSON name>-<timestamp>/",
        "generate.split_by_color": "Split by color (recommended for rerunning one color)",
        "generate.button": "Generate",
        "serial.group": "2. Serial and Controller",
        "serial.port": "Port",
        "serial.refresh": "Refresh Ports",
        "serial.match": "Pair Controller",
        "draw.group": "3. Draw",
        "draw.button": "Start Drawing",
        "draw.cancel": "Cancel",
        "draw.cancel_tooltip": (
            "Stop sending more drawing macros; queued SwiCC frames may still run briefly."
        ),
        "draw.disabled_tooltip": "Generate macros before starting drawing.",
        "draw.enabled_tooltip": "Send the currently generated drawing files.",
        "draw.current_file": "Current file: -",
        "draw.current_file_detail": "Current file: %index / %total · %name",
        "file_dialog.json_title": "Choose Living the Grid JSON",
        "file_dialog.json_filter": "JSON files (*.json)",
        "status.ready": "Ready",
        "status.generating": "Generating macros...",
        "status.loading_json": "Loading JSON...",
        "status.planning_macros": "Planning macros...",
        "status.writing_output": "Writing output...",
        "status.generated": "Generated",
        "status.pairing": "Pairing controller...",
        "status.pairing_drawing": "Pairing and drawing...",
        "status.drawing": "Drawing...",
        "status.cancelling": "Cancelling...",
        "status.cancelled": "Cancelled",
        "status.done": "Done",
        "status.failed": "Failed",
        "error.title": "Tomodachi Macrogen",
        "error.read_json": "Could not read JSON: %error",
        "error.serial_unavailable": "Serial port unavailable: %error",
        "error.no_json": "Choose a Living the Grid JSON first.",
        "error.no_port": "Choose a serial port first.",
        "error.no_files": "Generate macros first.",
        "error.open_living_grid": "Could not open Living the Grid.",
        "generation.meta": "%out_dir\n%files files, %lines lines, %frames frames",
        "progress.transfer": "%percent  queue=%queue  ETA %eta",
    },
}

_CONFIGURED = False


def configure_i18n(locale: str = DEFAULT_LOCALE) -> None:
    global _CONFIGURED
    if not _CONFIGURED:
        i18n.set("fallback", "en")
        i18n.set("error_on_missing_placeholder", True)
        for language, values in TRANSLATIONS.items():
            for key, value in values.items():
                i18n.add_translation(f"gui.{key}", value, locale=language)
        _CONFIGURED = True
    set_locale(locale)


def set_locale(locale: str) -> None:
    if locale not in {key for key, _label in LOCALE_OPTIONS}:
        locale = DEFAULT_LOCALE
    i18n.set("locale", locale)


def current_locale() -> str:
    value = i18n.get("locale")
    return str(value or DEFAULT_LOCALE)


def tr(key: str, **kwargs: object) -> str:
    return str(i18n.t(f"gui.{key}", **kwargs))
