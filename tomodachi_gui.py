import sys
import time
from html import escape
from io import BytesIO
from pathlib import Path

from PIL import Image

from src.gui_i18n import LOCALE_OPTIONS, configure_i18n, current_locale, set_locale, tr
from src.gui_theme import build_theme_style
from src.resources import RUN_README_EN_HTML, RUN_README_HTML
from swicc_runner import TransferProgress, import_serial_tools
from tomodachi_macrogen import GenerationResult

LIVING_THE_GRID_URL = "https://living-the-grid.com/"


def main() -> int:
    try:
        from PyQt6.QtCore import QObject, Qt, QThread, QUrl
        from PyQt6.QtGui import QActionGroup, QDesktopServices, QFont, QPixmap
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QFileDialog,
            QFrame,
            QGridLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMainWindow,
            QMessageBox,
            QProgressBar,
            QPushButton,
            QSizePolicy,
            QTextBrowser,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as error:
        raise SystemExit(f"PyQt6 import failed: {error}. Run `uv sync` first.") from error

    from src.gui_workers import GenerateWorker, TransferWorker, format_duration

    configure_i18n()

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.input_path: Path | None = None
            self.result: GenerationResult | None = None
            self.current_pixmap: QPixmap | None = None
            self.preview_info: dict[str, object] | None = None
            self.generation_info: dict[str, object] | None = None
            self.status_key: str | None = "status.ready"
            self.status_kwargs: dict[str, object] = {}
            self.current_theme = "light"
            self.link_color = "#21666c"
            self.threads: list[QThread] = []
            self.workers: list[QObject] = []
            self.readme_windows: list[QTextBrowser] = []

            self.resize(1120, 740)
            self.setMinimumSize(960, 640)
            self._build_ui()
            self._build_menu()
            self.refresh_ports()

        def _build_ui(self) -> None:
            root = QWidget()
            root_layout = QHBoxLayout(root)
            root_layout.setContentsMargins(22, 22, 22, 22)
            root_layout.setSpacing(18)
            self.setCentralWidget(root)

            preview_card = QFrame()
            preview_card.setObjectName("PreviewCard")
            preview_card.setMinimumWidth(410)
            preview_layout = QVBoxLayout(preview_card)
            preview_layout.setContentsMargins(22, 22, 22, 22)
            preview_layout.setSpacing(14)

            self.preview_title = QLabel()
            self.preview_title.setObjectName("SectionTitle")
            self.preview_label = QLabel()
            self.preview_label.setObjectName("PreviewLabel")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            self.preview_label.setMinimumSize(360, 360)
            self.meta_label = QLabel()
            self.meta_label.setObjectName("Muted")
            self.meta_label.setWordWrap(True)

            preview_layout.addWidget(self.preview_title)
            preview_layout.addWidget(self.preview_label, 1)
            preview_layout.addWidget(self.meta_label)
            root_layout.addWidget(preview_card, 4)

            right = QFrame()
            right.setObjectName("ControlCard")
            right_layout = QVBoxLayout(right)
            right_layout.setContentsMargins(22, 22, 22, 22)
            right_layout.setSpacing(12)
            root_layout.addWidget(right, 6)

            hero_row = QHBoxLayout()
            self.hero_label = QLabel()
            self.hero_label.setObjectName("Hero")
            hero_row.addWidget(self.hero_label, 1)
            self.subtitle_label = QLabel()
            self.subtitle_label.setObjectName("Muted")
            self.subtitle_label.setWordWrap(True)
            right_layout.addLayout(hero_row)
            right_layout.addWidget(self.subtitle_label)
            self.living_grid_link = QLabel()
            self.living_grid_link.setObjectName("ExternalLink")
            self.living_grid_link.setTextFormat(Qt.TextFormat.RichText)
            self.living_grid_link.setOpenExternalLinks(False)
            self.living_grid_link.setTextInteractionFlags(
                Qt.TextInteractionFlag.LinksAccessibleByMouse
                | Qt.TextInteractionFlag.LinksAccessibleByKeyboard,
            )
            self.living_grid_link.linkActivated.connect(
                lambda _url: self.open_living_grid(),
            )
            right_layout.addWidget(self.living_grid_link)

            self.generate_group = QGroupBox()
            generate_layout = QGridLayout(self.generate_group)
            generate_layout.setColumnStretch(1, 1)
            self.input_edit = QLineEdit()
            self.input_button = QPushButton()
            self.input_button.clicked.connect(self.choose_json)
            self.split_color_check = QCheckBox()
            self.split_color_check.setChecked(True)
            self.generate_button = QPushButton()
            self.generate_button.setObjectName("PrimaryButton")
            self.generate_button.clicked.connect(self.start_generation)
            self.input_text_label = QLabel()
            self.output_text_label = QLabel()
            self.output_hint_label = QLabel()

            generate_layout.addWidget(self.input_text_label, 0, 0)
            generate_layout.addWidget(self.input_edit, 0, 1)
            generate_layout.addWidget(self.input_button, 0, 2)
            generate_layout.addWidget(self.output_text_label, 1, 0)
            generate_layout.addWidget(self.output_hint_label, 1, 1, 1, 2)
            generate_layout.addWidget(self.split_color_check, 2, 1, 1, 2)
            generate_layout.addWidget(self.generate_button, 3, 2)
            right_layout.addWidget(self.generate_group)

            self.serial_group = QGroupBox()
            serial_layout = QGridLayout(self.serial_group)
            serial_layout.setColumnStretch(1, 1)
            self.port_combo = QComboBox()
            self.port_combo.setEditable(True)
            self.refresh_button = QPushButton()
            self.refresh_button.clicked.connect(self.refresh_ports)
            self.match_button = QPushButton()
            self.match_button.clicked.connect(self.start_match)
            self.port_text_label = QLabel()
            serial_layout.addWidget(self.port_text_label, 0, 0)
            serial_layout.addWidget(self.port_combo, 0, 1)
            serial_layout.addWidget(self.refresh_button, 0, 2)
            serial_layout.addWidget(self.match_button, 1, 2)
            right_layout.addWidget(self.serial_group)

            self.draw_group = QGroupBox()
            draw_layout = QVBoxLayout(self.draw_group)
            self.current_file_label = QLabel()
            self.current_file_label.setObjectName("Muted")
            self.file_list = QListWidget()
            self.file_list.setMinimumHeight(92)
            self.file_list.setMaximumHeight(150)
            self.file_list.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            self.draw_button = QPushButton()
            self.draw_button.setObjectName("PrimaryButton")
            self.draw_button.clicked.connect(self.start_draw)
            self.open_readme_button = QPushButton()
            self.open_readme_button.clicked.connect(self.open_run_readme)
            self.open_readme_button.setEnabled(False)
            self.cancel_draw_button = QPushButton()
            self.cancel_draw_button.clicked.connect(self.cancel_draw)
            self.update_draw_button_enabled()
            self.cancel_draw_button.setEnabled(False)
            button_row = QHBoxLayout()
            button_row.addWidget(self.open_readme_button)
            button_row.addWidget(self.draw_button, 1)
            button_row.addWidget(self.cancel_draw_button)
            draw_layout.addWidget(self.current_file_label)
            draw_layout.addWidget(self.file_list)
            draw_layout.addLayout(button_row)
            right_layout.addWidget(self.draw_group)

            progress_row = QHBoxLayout()
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(0)
            self.status_label = QLabel()
            self.status_label.setObjectName("Muted")
            progress_row.addWidget(self.progress_bar, 1)
            progress_row.addWidget(self.status_label)
            right_layout.addLayout(progress_row)

            app = QApplication.instance()
            if app is not None:
                app.setFont(QFont("Segoe UI Variable", 10))
            self.retranslate_ui()
            self.apply_theme("light")

        def _build_menu(self) -> None:
            self.view_menu = self.menuBar().addMenu("")
            self.language_menu = self.view_menu.addMenu("")
            self.theme_menu = self.view_menu.addMenu("")

            self.language_group = QActionGroup(self)
            self.language_group.setExclusive(True)
            self.language_actions = {}
            for locale, label in LOCALE_OPTIONS:
                action = self.language_menu.addAction(label)
                action.setCheckable(True)
                action.setData(locale)
                self.language_group.addAction(action)
                self.language_actions[locale] = action
            self.language_actions["zh"].setChecked(True)
            self.language_group.triggered.connect(self.change_language)

            self.theme_group = QActionGroup(self)
            self.theme_group.setExclusive(True)
            self.theme_actions = {}
            for theme in ("light", "dark"):
                action = self.theme_menu.addAction("")
                action.setCheckable(True)
                action.setData(theme)
                self.theme_group.addAction(action)
                self.theme_actions[theme] = action
            self.theme_actions["light"].setChecked(True)
            self.theme_group.triggered.connect(self.change_theme)
            self.retranslate_ui()

        def change_language(self, action: object) -> None:
            locale = action.data() if hasattr(action, "data") else "zh"
            set_locale(str(locale or "zh"))
            self.retranslate_ui()

        def change_theme(self, action: object) -> None:
            theme = action.data() if hasattr(action, "data") else "light"
            self.apply_theme(str(theme or "light"))

        def retranslate_ui(self) -> None:
            self.setWindowTitle(tr("app.title"))
            if hasattr(self, "view_menu"):
                self.view_menu.setTitle(tr("menu.view"))
                self.language_menu.setTitle(tr("menu.language"))
                self.theme_menu.setTitle(tr("menu.theme"))
                self.theme_actions["light"].setText(tr("theme.light"))
                self.theme_actions["dark"].setText(tr("theme.dark"))
            self.preview_title.setText(tr("preview.title"))
            self.preview_label.setText(tr("preview.empty"))
            self.hero_label.setText(tr("hero.title"))
            self.subtitle_label.setText(tr("hero.subtitle"))
            self.generate_group.setTitle(tr("generate.group"))
            self.input_text_label.setText(tr("generate.input"))
            self.output_text_label.setText(tr("generate.output"))
            self.input_edit.setPlaceholderText(tr("generate.input_placeholder"))
            self.input_button.setText(tr("generate.choose_json"))
            self.update_living_grid_link()
            self.output_hint_label.setText(tr("generate.output_hint"))
            self.split_color_check.setText(tr("generate.split_by_color"))
            self.generate_button.setText(tr("generate.button"))
            self.serial_group.setTitle(tr("serial.group"))
            self.port_text_label.setText(tr("serial.port"))
            self.refresh_button.setText(tr("serial.refresh"))
            self.match_button.setText(tr("serial.match"))
            self.draw_group.setTitle(tr("draw.group"))
            self.draw_button.setText(tr("draw.button"))
            self.open_readme_button.setText(tr("draw.open_readme"))
            self.open_readme_button.setToolTip(tr("draw.open_readme_tooltip"))
            self.cancel_draw_button.setText(tr("draw.cancel"))
            self.cancel_draw_button.setToolTip(tr("draw.cancel_tooltip"))
            self.update_draw_button_enabled()
            self.update_open_readme_button_enabled()
            self.update_current_file_label()
            self.update_meta_label()
            self.update_status_label()

        def update_living_grid_link(self) -> None:
            label = escape(tr("generate.open_living_grid"))
            self.living_grid_link.setText(
                '<a style="'
                f"color: {self.link_color}; "
                'text-decoration: underline;" '
                f'href="{LIVING_THE_GRID_URL}">{label}</a>',
            )
            self.living_grid_link.setToolTip(tr("generate.open_living_grid_tooltip"))

        def apply_theme(self, theme: str) -> None:
            self.current_theme = theme
            if hasattr(self, "theme_actions") and theme in self.theme_actions:
                self.theme_actions[theme].setChecked(True)
            style = build_theme_style(theme)
            self.link_color = style.link_color
            self.setStyleSheet(style.stylesheet)
            if hasattr(self, "living_grid_link"):
                self.update_living_grid_link()

        def choose_json(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("file_dialog.json_title"),
                str(Path.cwd()),
                tr("file_dialog.json_filter"),
            )
            if not path:
                return
            self.input_path = Path(path)
            self.input_edit.setText(path)
            self.load_json_preview(self.input_path)

        def open_living_grid(self) -> None:
            if not QDesktopServices.openUrl(QUrl(LIVING_THE_GRID_URL)):
                self.show_error(tr("error.open_living_grid"))

        def open_run_readme(self) -> None:
            if self.result is None:
                self.show_error(tr("error.no_files"))
                return
            filename = "README_RUN.html" if current_locale() == "zh" else "README_RUN-en.html"
            readme_path = self.result.out_dir / filename
            if not readme_path.exists():
                readme_path = RUN_README_HTML if current_locale() == "zh" else RUN_README_EN_HTML
            try:
                html = readme_path.read_text(encoding="utf-8")
            except OSError:
                self.show_error(tr("error.open_readme"))
                return
            browser = QTextBrowser(self)
            browser.setWindowTitle(tr("draw.open_readme"))
            browser.setOpenExternalLinks(True)
            browser.setSearchPaths([str(readme_path.parent)])
            browser.setHtml(html)
            browser.resize(760, 680)
            browser.destroyed.connect(
                lambda _object=None, window=browser: self.cleanup_readme_window(window)
            )
            self.readme_windows.append(browser)
            browser.show()

        def cleanup_readme_window(self, window: object) -> None:
            if window in self.readme_windows:
                self.readme_windows.remove(window)

        def load_json_preview(self, path: Path) -> None:
            try:
                from src.living_grid import load_living_grid_json

                grid = load_living_grid_json(path)
            except Exception as error:  # noqa: BLE001 - invalid user JSON should be visible.
                self.show_error(tr("error.read_json", error=error))
                return
            self.set_preview_image(grid.preview)
            palette_source = (
                "game" if all(entry.game is not None for entry in grid.palette) else "auto"
            )
            self.generation_info = None
            self.preview_info = {
                "name": path.name,
                "width": grid.width,
                "height": grid.height,
                "brush_px": grid.brush_px,
                "colors": len(grid.palette),
                "palette": palette_source,
            }
            self.update_meta_label()

        def set_preview_image(self, image: Image.Image) -> None:
            buffer = BytesIO()
            image.convert("RGBA").save(buffer, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue(), "PNG")
            self.current_pixmap = pixmap
            self.update_preview_pixmap()

        def update_preview_pixmap(self) -> None:
            if self.current_pixmap is None:
                return
            scaled = self.current_pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            self.preview_label.setPixmap(scaled)

        def resizeEvent(self, event: object) -> None:
            super().resizeEvent(event)
            self.update_preview_pixmap()

        def refresh_ports(self) -> None:
            current = self.port_combo.currentText().strip()
            self.port_combo.clear()
            try:
                ports = list(import_serial_tools().comports())
            except Exception as error:  # noqa: BLE001 - driver/import errors should be surfaced.
                self.set_status("error.serial_unavailable", error=error)
                return
            for port in ports:
                suffix = f" - {port.description}" if port.description else ""
                self.port_combo.addItem(f"{port.device}{suffix}", port.device)
            if current:
                index = self.port_combo.findText(current)
                if index >= 0:
                    self.port_combo.setCurrentIndex(index)
                else:
                    self.port_combo.setEditText(current)
            elif ports:
                self.port_combo.setCurrentIndex(0)

        def selected_port(self) -> str:
            data = self.port_combo.currentData()
            if data:
                return str(data)
            text = self.port_combo.currentText().strip()
            return text.split(" - ", 1)[0]

        def start_generation(self) -> None:
            input_text = self.input_edit.text().strip()
            if not input_text:
                self.show_error(tr("error.no_json"))
                return
            input_path = Path(input_text)
            self.set_busy(True, "status.generating")
            worker = GenerateWorker(input_path, self.split_color_check.isChecked())
            thread = self.start_worker(worker)
            thread.started.connect(worker.run)
            worker.status.connect(self.set_status)
            worker.finished.connect(self.on_generation_finished)
            worker.failed.connect(self.on_worker_failed)
            worker.finished.connect(thread.quit)
            worker.failed.connect(thread.quit)
            thread.start()

        def on_generation_finished(self, result: object) -> None:
            try:
                if not isinstance(result, GenerationResult):
                    raise TypeError(f"unexpected generation result: {type(result).__name__}")
                self.result = result
                self.file_list.clear()
                self.current_file_label.setText(tr("draw.current_file"))
                for path in self.result.macro_files:
                    self.file_list.addItem(str(path))
                self.set_preview_from_file(self.result.preview_path)
                self.preview_info = None
                self.generation_info = {
                    "out_dir": self.result.out_dir,
                    "files": len(self.result.macro_files),
                    "lines": self.result.total_lines,
                    "frames": self.result.total_frames,
                }
                self.update_meta_label()
            except Exception as error:  # noqa: BLE001 - keep the GUI from staying busy.
                self.show_error(str(error))
            finally:
                self.set_busy(False, "status.generated")
                self.update_draw_button_enabled()
                self.update_open_readme_button_enabled()

        def set_preview_from_file(self, path: Path) -> None:
            try:
                with Image.open(path) as image:
                    self.set_preview_image(image)
            except Exception:
                return

        def start_match(self) -> None:
            port = self.selected_port()
            if not port:
                self.show_error(tr("error.no_port"))
                return
            self.start_transfer(port, [], match_controller=True, status_key="status.pairing")

        def start_draw(self) -> None:
            port = self.selected_port()
            if not port:
                self.show_error(tr("error.no_port"))
                return
            files = self.current_macro_files()
            if not files:
                self.show_error(tr("error.no_files"))
                return
            self.start_transfer(
                port,
                files,
                match_controller=False,
                status_key="status.drawing",
            )

        def cancel_draw(self) -> None:
            worker = self.active_transfer_worker()
            if worker is None:
                return
            worker.cancel()
            self.cancel_draw_button.setEnabled(False)
            self.set_status("status.cancelling")

        def current_macro_files(self) -> list[Path]:
            if self.result is not None:
                return self.result.macro_files
            return []

        def start_transfer(
            self,
            port: str,
            files: list[Path],
            *,
            match_controller: bool,
            status_key: str,
        ) -> None:
            self.progress_bar.setValue(0)
            worker = TransferWorker(port, files, match_controller=match_controller)
            thread = self.start_worker(worker)
            self.set_busy(True, status_key)
            thread.started.connect(worker.run)
            worker.progress.connect(self.on_transfer_progress)
            worker.finished.connect(lambda: self.set_busy(False, "status.done"))
            worker.cancelled.connect(lambda: self.set_busy(False, "status.cancelled"))
            worker.failed.connect(self.on_worker_failed)
            worker.finished.connect(thread.quit)
            worker.cancelled.connect(thread.quit)
            worker.failed.connect(thread.quit)
            thread.start()

        def on_transfer_progress(self, payload: object) -> None:
            assert isinstance(payload, TransferProgress)
            if payload.total_frames <= 0:
                return
            value = int(payload.sent_frames * 1000 / payload.total_frames)
            self.progress_bar.setValue(max(0, min(1000, value)))
            percent = payload.sent_frames * 100 / payload.total_frames
            queue = "-" if payload.queue_fill is None else str(payload.queue_fill)
            eta = self.estimate_eta(payload)
            self.update_current_file_label(payload)
            self.status_key = None
            if payload.cancelled:
                self.status_label.setText(tr("status.cancelled"))
                return
            self.status_label.setText(
                tr(
                    "progress.transfer",
                    percent=f"{percent:5.1f}%",
                    queue=queue,
                    eta=eta,
                )
            )

        def estimate_eta(self, payload: TransferProgress) -> str:
            if payload.done:
                return format_duration(0)
            worker = self.active_transfer_worker()
            if worker is None or worker.started_at is None or payload.sent_frames <= 0:
                return format_duration(None)
            elapsed = max(0.0, time.monotonic() - worker.started_at)
            frames_per_second = payload.sent_frames / elapsed if elapsed else 0.0
            if frames_per_second <= 0:
                return format_duration(None)
            remaining = max(0, payload.total_frames - payload.sent_frames)
            return format_duration(remaining / frames_per_second)

        def active_transfer_worker(self) -> TransferWorker | None:
            for worker in self.workers:
                if isinstance(worker, TransferWorker):
                    return worker
            return None

        def update_current_file_label(self, payload: TransferProgress | None = None) -> None:
            if payload is None or payload.current_file_index is None or payload.total_files is None:
                self.current_file_label.setText(tr("draw.current_file"))
                return
            self.current_file_label.setText(
                tr(
                    "draw.current_file_detail",
                    index=payload.current_file_index,
                    total=payload.total_files,
                    name=payload.current_file or "",
                )
            )

        def start_worker(self, worker: QObject) -> QThread:
            thread = QThread(self)
            worker.moveToThread(thread)
            self.threads.append(thread)
            self.workers.append(worker)
            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(lambda: self.cleanup_worker(worker))
            thread.finished.connect(lambda: self.cleanup_thread(thread))
            return thread

        def cleanup_worker(self, worker: QObject) -> None:
            if worker in self.workers:
                self.workers.remove(worker)

        def cleanup_thread(self, thread: QThread) -> None:
            if thread in self.threads:
                self.threads.remove(thread)
            thread.deleteLater()

        def on_worker_failed(self, message: str) -> None:
            self.set_busy(False, "status.failed")
            self.show_error(message)

        def set_busy(self, busy: bool, status_key: str) -> None:
            self.generate_button.setDisabled(busy)
            self.match_button.setDisabled(busy)
            self.update_draw_button_enabled(force_disabled=busy)
            self.cancel_draw_button.setEnabled(
                busy
                and status_key == "status.drawing"
                and self.active_transfer_worker() is not None
            )
            self.set_status(status_key)

        def update_draw_button_enabled(self, *, force_disabled: bool = False) -> None:
            has_files = self.result is not None and bool(self.result.macro_files)
            enabled = has_files and not force_disabled
            self.draw_button.setEnabled(enabled)
            self.draw_button.setToolTip(
                tr("draw.enabled_tooltip") if has_files else tr("draw.disabled_tooltip")
            )

        def update_open_readme_button_enabled(self) -> None:
            self.open_readme_button.setEnabled(self.result is not None)

        def set_status(self, key: str, **kwargs: object) -> None:
            self.status_key = key
            self.status_kwargs = kwargs
            self.update_status_label()

        def update_status_label(self) -> None:
            if self.status_key is not None:
                self.status_label.setText(tr(self.status_key, **self.status_kwargs))

        def update_meta_label(self) -> None:
            if self.generation_info is not None:
                self.meta_label.setText(tr("generation.meta", **self.generation_info))
                return
            if self.preview_info is not None:
                self.meta_label.setText(tr("preview.meta", **self.preview_info))
                return
            self.meta_label.setText(tr("preview.unloaded"))

        def show_error(self, message: str) -> None:
            QMessageBox.critical(self, tr("error.title"), message)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
