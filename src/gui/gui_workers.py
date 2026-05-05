import time
from pathlib import Path
from threading import Event

from PyQt6.QtCore import QObject, pyqtSignal

from tomodachi_macrogen import (
    GenerationOptions,
    SerialOptions,
    generate_macros,
    send_macro_files,
)


class GenerateWorker(QObject):
    status = pyqtSignal(str)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, input_path: Path, *, enable_diagonal_movement: bool = False) -> None:
        super().__init__()
        self.input_path = input_path
        self.enable_diagonal_movement = enable_diagonal_movement

    def run(self) -> None:
        try:
            result = generate_macros(
                self.input_path,
                GenerationOptions(enable_diagonal_movement=self.enable_diagonal_movement),
                progress_callback=self.status.emit,
            )
        except Exception as error:  # noqa: BLE001 - surface worker errors in the GUI.
            self.failed.emit(str(error))
            return
        self.finished.emit(result)


class TransferWorker(QObject):
    progress = pyqtSignal(object)
    finished = pyqtSignal()
    cancelled = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(
        self,
        port: str,
        files: list[Path],
        *,
        match_controller: bool,
    ) -> None:
        super().__init__()
        self.port = port
        self.files = files
        self.match_controller = match_controller
        self.started_at: float | None = None
        self.cancel_event = Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        self.started_at = time.monotonic()
        try:
            send_macro_files(
                port=self.port,
                files=self.files,
                match_controller=self.match_controller,
                serial_options=SerialOptions(),
                progress_callback=self.progress.emit,
                should_cancel=self.cancel_event.is_set,
                show_progress_bar=False,
            )
        except Exception as error:  # noqa: BLE001 - serial failures need to reach the UI.
            self.failed.emit(str(error))
            return
        if self.cancel_event.is_set():
            self.cancelled.emit()
            return
        self.finished.emit()
