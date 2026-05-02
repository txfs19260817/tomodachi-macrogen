import argparse
import glob
import re
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTROLLER_MATCH_MACRO = """{A} 10
{} 60
{L1 R1} 10
{} 30
{A} 10
{} 10"""
MATCH_CONTROLLER_SETTLE_FRAMES = 4 * 60

MACRO_LINE_RE = re.compile(
    r"(?:{(?P<buttons>.*?)}\s*)?"
    r"(?:\((?P<lx>\d+)?\s*(?P<ly>\d+)?\s*(?P<rx>\d+)?\s*(?P<ry>\d+)?\))?"
    r"\s*(?P<frames>\d*)?"
)

BUTTON_ALIASES = {
    "ZL": "L2",
    "ZR": "R2",
    "LB": "L1",
    "RB": "R1",
    "PLUS": "+",
    "MINUS": "-",
    "HOME": "H",
    "CAPTURE": "C",
}


@dataclass(frozen=True)
class MacroCommand:
    buttons: str
    frames: int = 1
    lx: int = 128
    ly: int = 128
    rx: int = 128
    ry: int = 128
    source: str = ""


@dataclass(frozen=True)
class RunnerStats:
    file_count: int
    line_count: int
    frame_count: int


@dataclass(frozen=True)
class TransferProgress:
    sent_frames: int
    total_frames: int
    queue_fill: int | None = None
    done: bool = False
    cancelled: bool = False
    current_file_index: int | None = None
    total_files: int | None = None
    current_file: str | None = None


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_ports:
        return list_ports()

    if not args.port and not args.dry_run:
        parser.error("--port is required unless --dry-run or --list-ports is used")
    if not args.files and not args.match_controller:
        parser.error("provide at least one macro file or use --match-controller")

    file_paths = expand_macro_paths(args.files)
    if args.files and not file_paths:
        parser.error("no macro files matched the provided file arguments")
    commands = build_command_list(file_paths, match_controller=args.match_controller)

    stats = RunnerStats(
        file_count=len(file_paths),
        line_count=len(commands),
        frame_count=sum(command.frames for command in commands),
    )

    if args.dry_run:
        print_summary(stats, file_paths)
        for index, line in enumerate(iter_queue_lines(commands, include_neutral=True)):
            if index >= args.preview_lines:
                break
            print(line.rstrip())
        return 0

    run_serial_transfer(
        port=args.port,
        commands=commands,
        baud_rate=args.baud_rate,
        vsync_delay=args.vsync_delay,
        batch_size=args.batch_size,
        queue_threshold=args.queue_threshold,
        response_timeout=args.response_timeout,
        poll_interval=args.poll_interval,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send SwiCC macro txt files directly over a serial port."
    )
    parser.add_argument("files", nargs="*", help="Macro txt files or glob patterns")
    parser.add_argument("--port", help="Serial port, for example COM5 or /dev/ttyACM0")
    parser.add_argument("--baud-rate", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--list-ports", action="store_true", help="List serial ports and exit")
    parser.add_argument("--match-controller", action="store_true", help="Send pairing macro first")
    parser.add_argument("--vsync-delay", type=int, default=-1, help="-1 disables VSYNC delay")
    parser.add_argument("--batch-size", type=int, default=60, help="Max +Q lines to send per batch")
    parser.add_argument(
        "--queue-threshold",
        type=int,
        default=60,
        help="Send the next batch when SwiCC queue fill is below this value",
    )
    parser.add_argument(
        "--response-timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for a +GQF response before failing",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.25,
        help="Seconds between queue fill checks",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse and print without serial I/O")
    parser.add_argument(
        "--preview-lines",
        type=int,
        default=12,
        help="Number of encoded +Q lines to show in --dry-run",
    )
    return parser


def list_ports() -> int:
    serial_tools = import_serial_tools()
    ports = list(serial_tools.comports())
    if not ports:
        print("No serial ports found.")
        return 0
    for port in ports:
        details = f" - {port.description}" if port.description else ""
        print(f"{port.device}{details}")
    return 0


def expand_macro_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern) if glob.has_magic(pattern) else [pattern]
        for match in matches:
            path = Path(match)
            if path.is_file():
                paths.append(path)
    unique = {path.resolve(): path for path in paths}
    return sorted(unique.values(), key=natural_path_key)


def natural_path_key(path: Path) -> list[int | str]:
    parts = re.split(r"(\d+)", path.name.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def read_macro_files(paths: list[Path]) -> list[MacroCommand]:
    commands: list[MacroCommand] = []
    for path in paths:
        commands.extend(parse_macro_text(path.read_text(encoding="utf-8"), source=str(path)))
    return commands


def build_command_list(
    paths: list[Path],
    *,
    match_controller: bool,
) -> list[MacroCommand]:
    commands: list[MacroCommand] = []
    if match_controller:
        commands.extend(parse_macro_text(CONTROLLER_MATCH_MACRO, source="controller-match"))
        if paths:
            commands.append(
                MacroCommand(
                    buttons="",
                    frames=MATCH_CONTROLLER_SETTLE_FRAMES,
                    source="controller-match-settle",
                )
            )
    commands.extend(read_macro_files(paths))
    return commands


def parse_macro_text(text: str, *, source: str = "") -> list[MacroCommand]:
    commands: list[MacroCommand] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        command = parse_macro_line(raw_line, source=f"{source}:{line_number}" if source else "")
        if command is not None:
            commands.append(command)
    return commands


def parse_macro_line(raw_line: str, *, source: str = "") -> MacroCommand | None:
    line = raw_line.split(";", 1)[0].strip()
    if not line:
        return None
    match = MACRO_LINE_RE.fullmatch(line)
    if not match:
        raise ValueError(f"Invalid macro line {source or ''}: {raw_line!r}")

    frames = int(match.group("frames") or "1")
    if frames <= 0:
        raise ValueError(f"Macro frame count must be positive at {source or raw_line!r}")

    values = {
        key: _parse_stick_value(match.group(key), source=source or raw_line)
        for key in ("lx", "ly", "rx", "ry")
    }
    return MacroCommand(
        buttons=normalize_button_string(match.group("buttons") or ""),
        frames=frames,
        lx=values["lx"],
        ly=values["ly"],
        rx=values["rx"],
        ry=values["ry"],
        source=source,
    )


def _parse_stick_value(value: str | None, *, source: str) -> int:
    if value is None or value == "":
        return 128
    parsed = int(value)
    if parsed < 0 or parsed > 255:
        raise ValueError(f"Stick value must be in 0..255 at {source!r}")
    return parsed


def normalize_button_string(buttons: str) -> str:
    normalized = []
    for token in re.split(r"[\s,]+", buttons.strip().upper()):
        if not token:
            continue
        normalized.append(BUTTON_ALIASES.get(token, token))
    return " ".join(dict.fromkeys(normalized))


def convert_button_string(buttons: str) -> tuple[int, int, int]:
    tokens = set(normalize_button_string(buttons).split())
    button_low = 0
    button_high = 0
    hat = 8

    for token, bit in {
        "Y": 1,
        "B": 2,
        "A": 4,
        "X": 8,
        "L1": 16,
        "R1": 32,
        "L2": 64,
        "R2": 128,
    }.items():
        if token in tokens:
            button_low |= bit

    for token, bit in {
        "-": 1,
        "+": 2,
        "SL": 4,
        "SR": 8,
        "H": 16,
        "C": 32,
    }.items():
        if token in tokens:
            button_high |= bit

    diagonal = True
    if {"U", "R"} <= tokens:
        hat = 1
    elif {"D", "R"} <= tokens:
        hat = 3
    elif {"D", "L"} <= tokens:
        hat = 5
    elif {"U", "L"} <= tokens:
        hat = 7
    else:
        diagonal = False

    if not diagonal:
        if "U" in tokens:
            hat = 0
        if "R" in tokens:
            hat = 2
        if "D" in tokens:
            hat = 4
        if "L" in tokens:
            hat = 6

    return button_high, button_low, hat


def encode_macro_command(command: MacroCommand) -> str:
    button_high, button_low, hat = convert_button_string(command.buttons)
    return (
        "+Q "
        f"{byte_to_hex(button_high)}{byte_to_hex(button_low)}{byte_to_hex(hat)}"
        f"{byte_to_hex(command.lx)}{byte_to_hex(command.ly)}"
        f"{byte_to_hex(command.rx)}{byte_to_hex(command.ry)}\n"
    )


def byte_to_hex(value: int) -> str:
    return f"{max(0, min(255, value)):02X}"


def iter_queue_lines(
    commands: Iterable[MacroCommand],
    *,
    include_neutral: bool,
) -> Iterator[str]:
    if include_neutral:
        yield from _repeat_encoded(MacroCommand(buttons="", frames=2), 2)
    for command in commands:
        yield from _repeat_encoded(command, command.frames)
    if include_neutral:
        yield from _repeat_encoded(MacroCommand(buttons="", frames=2), 2)


def _repeat_encoded(command: MacroCommand, frames: int) -> Iterator[str]:
    encoded = encode_macro_command(command)
    for _ in range(frames):
        yield encoded


def print_summary(stats: RunnerStats, file_paths: list[Path]) -> None:
    print(f"Files: {stats.file_count}")
    print(f"Macro lines: {stats.line_count}")
    print(f"Frames: {stats.frame_count}")
    if file_paths:
        print("File order:")
        for path in file_paths:
            print(f"  {path}")
    print("Encoded preview:")


def run_serial_transfer(
    *,
    port: str,
    commands: list[MacroCommand],
    baud_rate: int,
    vsync_delay: int,
    batch_size: int,
    queue_threshold: int,
    response_timeout: float,
    poll_interval: float,
    progress_callback: Callable[[TransferProgress], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
    show_progress_bar: bool = True,
) -> None:
    serial_module = import_serial()
    total_frames = sum(command.frames for command in commands) + 4
    queue = iter_queue_lines(commands, include_neutral=True)
    tracker = FileProgressTracker(commands)
    sent_frames = 0

    with serial_module.Serial(port, baud_rate, timeout=0.1, write_timeout=2) as serial_port:
        progress = make_progress_bar(total_frames) if show_progress_bar else None
        try:
            configure_swicc(serial_port, vsync_delay)
            sent_now = send_next_batch(serial_port, queue, batch_size, should_cancel)
            sent_frames += sent_now
            update_transfer_progress(
                progress,
                progress_callback,
                sent_frames=sent_frames,
                total_frames=total_frames,
                delta=sent_now,
                file_status=tracker.update(sent_frames),
            )
            write_serial_line(serial_port, "+GQF \n")

            while True:
                if should_cancel is not None and should_cancel():
                    update_transfer_progress(
                        progress,
                        progress_callback,
                        sent_frames=sent_frames,
                        total_frames=total_frames,
                        queue_fill=None,
                        done=True,
                        cancelled=True,
                        file_status=tracker.update(sent_frames),
                    )
                    return
                fill = read_queue_fill(serial_port, response_timeout)
                update_transfer_progress(
                    progress,
                    progress_callback,
                    sent_frames=sent_frames,
                    total_frames=total_frames,
                    queue_fill=fill,
                    file_status=tracker.update(sent_frames),
                )
                if fill < queue_threshold:
                    sent_now = send_next_batch(serial_port, queue, batch_size, should_cancel)
                    sent_frames += sent_now
                    update_transfer_progress(
                        progress,
                        progress_callback,
                        sent_frames=sent_frames,
                        total_frames=total_frames,
                        delta=sent_now,
                        queue_fill=fill,
                        file_status=tracker.update(sent_frames),
                    )
                    if sent_now == 0 and fill <= 1:
                        sent_frames = total_frames
                        progress_delta = 0
                        if progress is not None:
                            progress_delta = total_frames - progress.n
                        update_transfer_progress(
                            progress,
                            progress_callback,
                            sent_frames=sent_frames,
                            total_frames=total_frames,
                            delta=progress_delta,
                            queue_fill=fill,
                            done=True,
                            cancelled=False,
                            file_status=tracker.update(sent_frames),
                        )
                        return
                time.sleep(poll_interval if fill >= queue_threshold else min(poll_interval, 0.1))
                write_serial_line(serial_port, "+GQF \n")
        finally:
            if progress is not None:
                progress.close()


def update_transfer_progress(
    progress: Any | None,
    progress_callback: Callable[[TransferProgress], None] | None,
    *,
    sent_frames: int,
    total_frames: int,
    delta: int = 0,
    queue_fill: int | None = None,
    done: bool = False,
    cancelled: bool = False,
    file_status: tuple[int, int, str] | None = None,
) -> None:
    if progress is not None:
        if delta:
            progress.update(delta)
        if queue_fill is not None:
            progress.set_postfix(queue=queue_fill)
    if progress_callback is not None:
        current_file_index = None
        total_files = None
        current_file = None
        if file_status is not None:
            current_file_index, total_files, current_file = file_status
        progress_callback(
            TransferProgress(
                sent_frames=sent_frames,
                total_frames=total_frames,
                queue_fill=queue_fill,
                done=done,
                cancelled=cancelled,
                current_file_index=current_file_index,
                total_files=total_files,
                current_file=current_file,
            )
        )


class FileProgressTracker:
    def __init__(self, commands: list[MacroCommand]) -> None:
        self.entries: list[tuple[int, int, str]] = []
        total = 2
        last_file = ""
        for command in commands:
            file_name = command_source_file(command.source)
            if file_name and file_name != last_file:
                self.entries.append((total, 0, file_name))
                last_file = file_name
            total += command.frames
        file_total = len(self.entries)
        self.entries = [
            (start_frame, index, file_name)
            for index, (start_frame, _unused, file_name) in enumerate(self.entries, start=1)
        ]
        self.total_files = file_total

    def update(self, sent_frames: int) -> tuple[int, int, str] | None:
        current: tuple[int, int, str] | None = None
        for start_frame, index, file_name in self.entries:
            if sent_frames >= start_frame:
                current = (index, self.total_files, file_name)
            else:
                break
        return current


def command_source_file(source: str) -> str | None:
    if not source or source.startswith("controller-match"):
        return None
    raw_path = source.rsplit(":", 1)[0]
    if not raw_path:
        return None
    return Path(raw_path).name


def configure_swicc(serial_port: Any, vsync_delay: int) -> None:
    write_serial_line(serial_port, "+VER 0\n")
    write_serial_line(serial_port, "+SLAG 0\n")
    if vsync_delay < 0:
        write_serial_line(serial_port, "+VSYNC 0\n")
        return
    write_serial_line(serial_port, "+VSYNC 1\n")
    write_serial_line(serial_port, f"+VSD {max(0, min(15000, vsync_delay)):04X}\n")


def send_next_batch(
    serial_port: Any,
    queue: Iterator[str],
    batch_size: int,
    should_cancel: Callable[[], bool] | None = None,
) -> int:
    sent = 0
    for _ in range(max(1, batch_size)):
        if should_cancel is not None and should_cancel():
            break
        try:
            write_serial_line(serial_port, next(queue))
        except StopIteration:
            break
        sent += 1
    return sent


def write_serial_line(serial_port: Any, line: str) -> None:
    serial_port.write(line.encode("ascii"))
    serial_port.flush()


def read_queue_fill(serial_port: Any, timeout_seconds: float) -> int:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        raw_line = serial_port.readline()
        if not raw_line:
            continue
        line = raw_line.decode("ascii", errors="replace").strip()
        if line.startswith("+GQF "):
            return int(line[5:].strip(), 16)
    raise TimeoutError("Timed out waiting for +GQF response from SwiCC")


def make_progress_bar(total_frames: int) -> Any:
    try:
        from tqdm import tqdm
    except ImportError as error:
        raise SystemExit("tqdm is required. Run `uv sync` first.") from error
    return tqdm(total=total_frames, unit="frame", dynamic_ncols=True, desc="SwiCC")


def import_serial() -> Any:
    try:
        import serial
    except ImportError as error:
        raise SystemExit("pyserial is required. Run `uv sync` first.") from error
    return serial


def import_serial_tools() -> Any:
    try:
        import serial.tools.list_ports
    except ImportError as error:
        raise SystemExit("pyserial is required. Run `uv sync` first.") from error
    return serial.tools.list_ports


if __name__ == "__main__":
    raise SystemExit(main())
