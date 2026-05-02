import tempfile
import unittest
from pathlib import Path

from tomodachi_macrogen import default_output_root, resolve_output_dir


class TestOutputDir(unittest.TestCase):
    def test_default_uses_input_filename_stem_with_timestamp(self) -> None:
        self.assertEqual(
            resolve_output_dir(Path("downloads/example.json"), timestamp="20260501-120000"),
            default_output_root() / "example-20260501-120000",
        )

    def test_existing_output_gets_numeric_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            existing = output_root / "example-20260501-120000"
            existing.mkdir(parents=True, exist_ok=True)
            self.assertEqual(
                resolve_output_dir(
                    Path("example.json"),
                    output_root=output_root,
                    timestamp="20260501-120000",
                ),
                output_root / "example-20260501-120000-2",
            )

    def test_frozen_windows_output_root_is_next_to_exe(self) -> None:
        self.assertEqual(
            default_output_root(
                frozen=True,
                executable=Path("D:/portable/tomodachi-gui/tomodachi-gui.exe"),
            ),
            Path("D:/portable/tomodachi-gui/out"),
        )

    def test_frozen_macos_output_root_is_next_to_app_bundle(self) -> None:
        self.assertEqual(
            default_output_root(
                frozen=True,
                executable=Path("D:/portable/tomodachi-gui.app/Contents/MacOS/tomodachi-gui"),
            ),
            Path("D:/portable/out"),
        )


if __name__ == "__main__":
    unittest.main()
