import os
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = (
    "config.default.json",
    "README_RUN.template.md",
    "README_RUN-en.template.md",
)


def main() -> int:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
