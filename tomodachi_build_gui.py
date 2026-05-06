import argparse
import os
import shutil
import sys
from pathlib import Path

from src.app.resources import BUNDLED_DATA_FILES

ROOT = Path(__file__).resolve().parent
DATA_FILES = BUNDLED_DATA_FILES
APP_ICON = (
    ROOT / "assets" / "app-icon.ico"
    if sys.platform == "win32"
    else ROOT / "assets" / "app-icon.png"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the portable PyQt6 GUI with PyInstaller.")
    parser.add_argument(
        "--keep-build",
        action="store_true",
        help="Keep PyInstaller build intermediates and the generated .spec file.",
    )
    return parser


def clean_intermediates() -> None:
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    spec_file = ROOT / "tomodachi-gui.spec"
    if spec_file.exists():
        spec_file.unlink()


def data_file_destination(relative_path: str) -> str:
    parent = Path(relative_path).parent
    return "." if str(parent) == "." else str(parent)


def main() -> int:
    args_namespace = build_parser().parse_args()

    import PyInstaller.__main__

    args = [
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        "tomodachi-gui",
        "--icon",
        str(APP_ICON),
    ]
    for relative_path in DATA_FILES:
        args.extend(
            [
                "--add-data",
                f"{ROOT / relative_path}{os.pathsep}{data_file_destination(relative_path)}",
            ]
        )
    args.append(str(ROOT / "tomodachi_gui.py"))
    PyInstaller.__main__.run(args)
    if not args_namespace.keep_build:
        clean_intermediates()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
