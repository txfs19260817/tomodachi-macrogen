import argparse
import os
import shutil
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = (
    "config.default.json",
    "README_RUN.template.md",
    "README_RUN-en.template.md",
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


def main() -> int:
    args_namespace = build_parser().parse_args()
    args = [
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        "tomodachi-gui",
    ]
    for relative_path in DATA_FILES:
        args.extend(["--add-data", f"{ROOT / relative_path}{os.pathsep}."])
    args.append(str(ROOT / "tomodachi_gui.py"))
    PyInstaller.__main__.run(args)
    if not args_namespace.keep_build:
        clean_intermediates()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
